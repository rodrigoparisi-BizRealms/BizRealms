"""BizRealms - Daily Business Dilemmas, Themed Tournaments & Reputation System"""
from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timedelta
from database import db
from utils import get_current_user
import uuid
import random
import hashlib

router = APIRouter()

# ==================== DAILY BUSINESS DILEMMAS ====================

DILEMMAS = [
    {
        "id": "cheap_supplier",
        "title": "Fornecedor Suspeito",
        "description": "Um fornecedor oferece materiais 50% mais baratos, mas a qualidade é duvidosa. Aceitar pode aumentar seus lucros OU causar problemas.",
        "icon": "cube-outline",
        "choices": [
            {"text": "Aceitar a oferta", "icon": "checkmark-circle", "effects": {"money_pct": 0.08, "reputation": -5, "xp": 15}, "result": "Lucro imediato! Mas sua reputação caiu um pouco."},
            {"text": "Recusar e manter qualidade", "icon": "shield-checkmark", "effects": {"money_pct": -0.02, "reputation": 10, "xp": 25}, "result": "Decisão sábia! Sua reputação cresceu entre os clientes."},
        ]
    },
    {
        "id": "employee_raise",
        "title": "Funcionário-Chave",
        "description": "Seu melhor funcionário quer um aumento de 30%. Se recusar, ele pode ir para o concorrente.",
        "icon": "people",
        "choices": [
            {"text": "Dar o aumento", "icon": "cash-outline", "effects": {"money_pct": -0.05, "reputation": 8, "xp": 20}, "result": "Funcionário motivado! Produtividade aumentou."},
            {"text": "Recusar o aumento", "icon": "close-circle", "effects": {"money_pct": 0.03, "reputation": -8, "xp": 10}, "result": "Economizou dinheiro, mas perdeu um talento importante."},
        ]
    },
    {
        "id": "expansion_risk",
        "title": "Oportunidade de Expansão",
        "description": "Surgiu uma chance de abrir filial em outra cidade. Alto investimento, mas potencial enorme.",
        "icon": "business",
        "choices": [
            {"text": "Investir na expansão", "icon": "rocket", "effects": {"money_pct": -0.15, "reputation": 12, "xp": 40}, "result": "Expansão arriscada! Mas sua marca agora é nacional."},
            {"text": "Focar no mercado atual", "icon": "home", "effects": {"money_pct": 0.05, "reputation": 3, "xp": 15}, "result": "Decisão conservadora. Lucro estável e seguro."},
        ]
    },
    {
        "id": "media_scandal",
        "title": "Escândalo na Mídia",
        "description": "Uma notícia falsa sobre sua empresa está circulando. Você pode processar ou ignorar.",
        "icon": "newspaper",
        "choices": [
            {"text": "Processar judicialmente", "icon": "hammer", "effects": {"money_pct": -0.08, "reputation": 15, "xp": 30}, "result": "Justiça feita! Processo ganho e reputação restaurada."},
            {"text": "Ignorar e seguir em frente", "icon": "eye-off", "effects": {"money_pct": 0, "reputation": -5, "xp": 10}, "result": "A notícia sumiu, mas alguns clientes ficaram desconfiados."},
        ]
    },
    {
        "id": "green_initiative",
        "title": "Iniciativa Verde",
        "description": "Uma ONG propõe parceria para tornar sua empresa sustentável. Custa caro mas melhora a imagem.",
        "icon": "leaf",
        "choices": [
            {"text": "Aderir ao programa verde", "icon": "leaf", "effects": {"money_pct": -0.10, "reputation": 20, "xp": 35}, "result": "Empresa sustentável! Novos clientes conscientes chegaram."},
            {"text": "Manter operações normais", "icon": "construct", "effects": {"money_pct": 0.03, "reputation": -3, "xp": 10}, "result": "Sem mudanças. Operação eficiente mas sem diferencial."},
        ]
    },
    {
        "id": "tech_upgrade",
        "title": "Modernização Tecnológica",
        "description": "Uma startup oferece automação que pode substituir 30% dos funcionários. Eficiência vs. empregos.",
        "icon": "hardware-chip",
        "choices": [
            {"text": "Automatizar processos", "icon": "flash", "effects": {"money_pct": 0.12, "reputation": -10, "xp": 25}, "result": "Eficiência disparou! Mas demissões geraram críticas."},
            {"text": "Investir em treinamento", "icon": "school", "effects": {"money_pct": -0.06, "reputation": 15, "xp": 30}, "result": "Equipe qualificada! Produtividade subiu organicamente."},
        ]
    },
    {
        "id": "competitor_merger",
        "title": "Proposta de Fusão",
        "description": "Um concorrente menor propõe fusão. Você ganha mercado mas perde autonomia parcial.",
        "icon": "git-merge",
        "choices": [
            {"text": "Aceitar a fusão", "icon": "link", "effects": {"money_pct": 0.15, "reputation": 5, "xp": 35}, "result": "Fusão concluída! Mercado expandido significativamente."},
            {"text": "Recusar e competir", "icon": "trophy", "effects": {"money_pct": -0.03, "reputation": 8, "xp": 20}, "result": "Independência mantida! Sua marca ficou mais forte."},
        ]
    },
    {
        "id": "charity_event",
        "title": "Evento Beneficente",
        "description": "Organizar um grande evento de caridade. Custa muito, mas a visibilidade é enorme.",
        "icon": "heart",
        "choices": [
            {"text": "Organizar o evento", "icon": "gift", "effects": {"money_pct": -0.12, "reputation": 25, "xp": 40}, "result": "Evento incrível! Sua reputação disparou na comunidade."},
            {"text": "Fazer doação discreta", "icon": "cash", "effects": {"money_pct": -0.03, "reputation": 8, "xp": 15}, "result": "Gesto nobre. Menos visível, mas igualmente importante."},
        ]
    },
    {
        "id": "patent_dispute",
        "title": "Disputa de Patente",
        "description": "Outra empresa está copiando seu produto. Processar custa caro mas protege sua inovação.",
        "icon": "document-lock",
        "choices": [
            {"text": "Processar por patente", "icon": "shield", "effects": {"money_pct": -0.10, "reputation": 12, "xp": 30}, "result": "Patente protegida! Concorrente parou de copiar."},
            {"text": "Inovar mais rápido", "icon": "bulb", "effects": {"money_pct": -0.04, "reputation": 10, "xp": 35}, "result": "Sua velocidade de inovação deixou a cópia obsoleta!"},
        ]
    },
    {
        "id": "influencer_deal",
        "title": "Parceria com Influencer",
        "description": "Um influencer famoso quer promover sua marca. É caro, mas pode viralizar.",
        "icon": "megaphone",
        "choices": [
            {"text": "Fechar parceria", "icon": "star", "effects": {"money_pct": -0.08, "reputation": 18, "xp": 30}, "result": "Viralização! Vendas subiram 40% na semana."},
            {"text": "Marketing tradicional", "icon": "newspaper", "effects": {"money_pct": -0.03, "reputation": 5, "xp": 15}, "result": "Resultado estável. Marketing seguro e previsível."},
        ]
    },
    {
        "id": "data_breach",
        "title": "Vazamento de Dados",
        "description": "Dados de clientes foram expostos. Você pode ser transparente ou tentar abafar.",
        "icon": "warning",
        "choices": [
            {"text": "Divulgar e corrigir", "icon": "megaphone", "effects": {"money_pct": -0.06, "reputation": 15, "xp": 30}, "result": "Transparência valorizada! Clientes confiaram mais."},
            {"text": "Resolver silenciosamente", "icon": "eye-off", "effects": {"money_pct": -0.02, "reputation": -15, "xp": 10}, "result": "Resolvido, mas se descobrirem... a confiança desaba."},
        ]
    },
    {
        "id": "price_war",
        "title": "Guerra de Preços",
        "description": "Concorrentes baixaram preços agressivamente. Entrar na guerra ou manter premium?",
        "icon": "trending-down",
        "choices": [
            {"text": "Baixar preços também", "icon": "pricetags", "effects": {"money_pct": -0.10, "reputation": -3, "xp": 15}, "result": "Volume de vendas subiu, mas margem despencou."},
            {"text": "Manter preço premium", "icon": "diamond", "effects": {"money_pct": 0.02, "reputation": 12, "xp": 25}, "result": "Posicionamento premium! Clientes fiéis permaneceram."},
        ]
    },
]

def _get_daily_dilemma_for_user(user_id: str) -> dict:
    """Get a deterministic daily dilemma based on date + user_id."""
    today = datetime.utcnow().strftime("%Y-%m-%d")
    seed = hashlib.md5(f"{today}:{user_id}".encode()).hexdigest()
    idx = int(seed, 16) % len(DILEMMAS)
    return DILEMMAS[idx]


@router.get("/dilemmas/daily")
async def get_daily_dilemma(current_user: dict = Depends(get_current_user)):
    """Get today's business dilemma for the player."""
    today = datetime.utcnow().strftime("%Y-%m-%d")
    
    # Check if already responded today
    existing = await db.dilemma_responses.find_one({
        "user_id": current_user['id'],
        "date": today,
    })
    
    dilemma = _get_daily_dilemma_for_user(current_user['id'])
    
    if existing:
        return {
            "dilemma": dilemma,
            "already_responded": True,
            "response": {
                "choice_index": existing['choice_index'],
                "effects": existing['effects'],
                "result_text": existing['result_text'],
            },
            "streak": existing.get('streak', 0),
        }
    
    # Count streak
    yesterday = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
    yesterday_resp = await db.dilemma_responses.find_one({
        "user_id": current_user['id'],
        "date": yesterday,
    })
    streak = (yesterday_resp.get('streak', 0) if yesterday_resp else 0)
    
    return {
        "dilemma": dilemma,
        "already_responded": False,
        "streak": streak,
    }


@router.post("/dilemmas/respond")
async def respond_to_dilemma(request: dict, current_user: dict = Depends(get_current_user)):
    """Submit a choice for today's dilemma."""
    choice_index = request.get('choice_index', 0)
    today = datetime.utcnow().strftime("%Y-%m-%d")
    
    existing = await db.dilemma_responses.find_one({
        "user_id": current_user['id'],
        "date": today,
    })
    if existing:
        raise HTTPException(status_code=400, detail="Você já respondeu o dilema de hoje!")
    
    dilemma = _get_daily_dilemma_for_user(current_user['id'])
    
    if choice_index < 0 or choice_index >= len(dilemma['choices']):
        raise HTTPException(status_code=400, detail="Escolha inválida.")
    
    choice = dilemma['choices'][choice_index]
    effects = choice['effects']
    
    # Apply effects
    user = await db.users.find_one({"id": current_user['id']})
    money = user.get('money', 0)
    money_change = round(money * effects.get('money_pct', 0), 2)
    rep_change = effects.get('reputation', 0)
    xp_change = effects.get('xp', 0)
    
    # Streak calculation
    yesterday = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
    yesterday_resp = await db.dilemma_responses.find_one({
        "user_id": current_user['id'],
        "date": yesterday,
    })
    streak = (yesterday_resp.get('streak', 0) + 1) if yesterday_resp else 1
    streak_bonus_xp = min(streak * 5, 50)  # Up to 50 bonus XP for streak
    
    new_money = max(0, money + money_change)
    current_rep = user.get('reputation', 50)
    new_rep = max(0, min(100, current_rep + rep_change))
    current_xp = user.get('experience_points', 0)
    total_xp = xp_change + streak_bonus_xp
    
    await db.users.update_one({"id": current_user['id']}, {"$set": {
        "money": new_money,
        "reputation": new_rep,
        "experience_points": current_xp + total_xp,
    }})
    
    # Save response
    await db.dilemma_responses.insert_one({
        "id": str(uuid.uuid4()),
        "user_id": current_user['id'],
        "date": today,
        "dilemma_id": dilemma['id'],
        "choice_index": choice_index,
        "effects": {"money_change": money_change, "reputation_change": rep_change, "xp_gained": total_xp},
        "result_text": choice['result'],
        "streak": streak,
        "created_at": datetime.utcnow(),
    })
    
    return {
        "success": True,
        "result_text": choice['result'],
        "effects": {
            "money_change": money_change,
            "reputation_change": rep_change,
            "xp_gained": total_xp,
            "streak": streak,
            "streak_bonus_xp": streak_bonus_xp,
        },
        "new_money": new_money,
        "new_reputation": new_rep,
    }


# ==================== THEMED TOURNAMENTS ====================

TOURNAMENT_THEMES = [
    {"id": "investor_week", "name": "Semana do Investidor", "icon": "trending-up", "color": "#4CAF50", "metric": "investment_profit", "description": "Quem lucrar mais com investimentos vence!"},
    {"id": "entrepreneur_challenge", "name": "Desafio do Empreendedor", "icon": "business", "color": "#2196F3", "metric": "companies_revenue", "description": "Quem gerar mais receita com empresas ganha!"},
    {"id": "real_estate_mogul", "name": "Magnata Imobiliário", "icon": "home", "color": "#FF9800", "metric": "asset_value", "description": "Quem acumular mais valor em imóveis vence!"},
    {"id": "savings_master", "name": "Mestre da Poupança", "icon": "wallet", "color": "#9C27B0", "metric": "money_saved", "description": "Quem economizar mais dinheiro no período ganha!"},
    {"id": "xp_hunter", "name": "Caçador de XP", "icon": "star", "color": "#FFD700", "metric": "xp_gained", "description": "Quem ganhar mais experiência vence!"},
]

def _get_current_tournament():
    """Get the current weekly tournament based on the week number."""
    now = datetime.utcnow()
    week_num = now.isocalendar()[1]
    idx = week_num % len(TOURNAMENT_THEMES)
    theme = TOURNAMENT_THEMES[idx]
    
    # Calculate start/end of week (Monday to Sunday)
    start = now - timedelta(days=now.weekday())
    start = start.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=6, hours=23, minutes=59, seconds=59)
    
    return {
        **theme,
        "week": f"{now.year}-W{week_num:02d}",
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "days_remaining": max(0, (end - now).days),
        "hours_remaining": max(0, int((end - now).total_seconds() / 3600)),
    }


@router.get("/tournaments/current")
async def get_current_tournament(current_user: dict = Depends(get_current_user)):
    """Get the current weekly themed tournament."""
    tournament = _get_current_tournament()
    week = tournament['week']
    
    # Get leaderboard for this tournament
    entries = await db.tournament_entries.find({"week": week}).sort("score", -1).to_list(50)
    
    leaderboard = []
    for i, e in enumerate(entries):
        user = await db.users.find_one({"id": e['user_id']})
        if user:
            leaderboard.append({
                "position": i + 1,
                "user_id": e['user_id'],
                "name": user.get('name', 'Jogador'),
                "avatar_color": user.get('avatar_color', 'blue'),
                "level": user.get('level', 1),
                "score": e['score'],
            })
    
    # Get user's entry
    user_entry = await db.tournament_entries.find_one({"week": week, "user_id": current_user['id']})
    user_position = next((i + 1 for i, e in enumerate(entries) if e['user_id'] == current_user['id']), None)
    
    # Prize pool for tournament
    total_participants = len(entries)
    prize_pool = 500 + (total_participants * 100)  # Base $500 + $100 per participant (in-game money)
    
    return {
        **tournament,
        "leaderboard": leaderboard[:10],
        "total_participants": total_participants,
        "user_score": user_entry['score'] if user_entry else 0,
        "user_position": user_position,
        "prize_pool": prize_pool,
        "prizes": [
            {"position": 1, "amount": round(prize_pool * 0.50), "label": "1º Lugar"},
            {"position": 2, "amount": round(prize_pool * 0.30), "label": "2º Lugar"},
            {"position": 3, "amount": round(prize_pool * 0.20), "label": "3º Lugar"},
        ],
    }


@router.post("/tournaments/update-score")
async def update_tournament_score(request: dict, current_user: dict = Depends(get_current_user)):
    """Update player's tournament score (called automatically on relevant actions)."""
    tournament = _get_current_tournament()
    week = tournament['week']
    score_delta = request.get('score', 0)
    
    existing = await db.tournament_entries.find_one({"week": week, "user_id": current_user['id']})
    
    if existing:
        await db.tournament_entries.update_one(
            {"week": week, "user_id": current_user['id']},
            {"$inc": {"score": score_delta}, "$set": {"updated_at": datetime.utcnow()}}
        )
    else:
        await db.tournament_entries.insert_one({
            "id": str(uuid.uuid4()),
            "user_id": current_user['id'],
            "week": week,
            "tournament_id": tournament['id'],
            "score": score_delta,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        })
    
    return {"success": True, "tournament": tournament['name'], "score_added": score_delta}


# ==================== REPUTATION / STARS SYSTEM ====================

REPUTATION_TIERS = [
    {"min": 0,  "max": 19, "tier": "Iniciante", "stars": 1, "color": "#9E9E9E", "icon": "star-outline", "perks": []},
    {"min": 20, "max": 39, "tier": "Confiável", "stars": 2, "color": "#8BC34A", "icon": "star-half", "perks": ["loan_discount_5"]},
    {"min": 40, "max": 59, "tier": "Respeitado", "stars": 3, "color": "#4CAF50", "icon": "star", "perks": ["loan_discount_10", "better_deals"]},
    {"min": 60, "max": 79, "tier": "Influente", "stars": 4, "color": "#2196F3", "icon": "star", "perks": ["loan_discount_15", "better_deals", "vip_investments"]},
    {"min": 80, "max": 100, "tier": "Lendário", "stars": 5, "color": "#FFD700", "icon": "star", "perks": ["loan_discount_20", "better_deals", "vip_investments", "exclusive_events"]},
]

def _get_reputation_tier(reputation: int) -> dict:
    for tier in REPUTATION_TIERS:
        if tier['min'] <= reputation <= tier['max']:
            return tier
    return REPUTATION_TIERS[0]


@router.get("/reputation/status")
async def get_reputation_status(current_user: dict = Depends(get_current_user)):
    """Get player's reputation status, tier, stars, and perks."""
    user = await db.users.find_one({"id": current_user['id']})
    reputation = user.get('reputation', 50)
    tier = _get_reputation_tier(reputation)
    
    # Calculate progress to next tier
    current_tier_idx = REPUTATION_TIERS.index(tier)
    next_tier = REPUTATION_TIERS[min(current_tier_idx + 1, len(REPUTATION_TIERS) - 1)]
    progress = 0
    if tier != next_tier:
        range_size = tier['max'] - tier['min'] + 1
        progress = ((reputation - tier['min']) / range_size) * 100
    else:
        progress = 100
    
    # History of reputation changes
    history = await db.dilemma_responses.find(
        {"user_id": current_user['id']}
    ).sort("created_at", -1).to_list(10)
    
    rep_history = []
    for h in history:
        effects = h.get('effects', {})
        rep_history.append({
            "date": h.get('date', ''),
            "dilemma_id": h.get('dilemma_id', ''),
            "reputation_change": effects.get('reputation_change', 0),
        })
    
    # Perk descriptions
    perk_descriptions = {
        "loan_discount_5": {"name": "Desconto em Empréstimos 5%", "icon": "cash", "description": "Juros reduzidos em 5%"},
        "loan_discount_10": {"name": "Desconto em Empréstimos 10%", "icon": "cash", "description": "Juros reduzidos em 10%"},
        "loan_discount_15": {"name": "Desconto em Empréstimos 15%", "icon": "cash", "description": "Juros reduzidos em 15%"},
        "loan_discount_20": {"name": "Desconto em Empréstimos 20%", "icon": "cash", "description": "Juros reduzidos em 20%"},
        "better_deals": {"name": "Negócios Melhores", "icon": "pricetag", "description": "Acesso a ofertas exclusivas"},
        "vip_investments": {"name": "Investimentos VIP", "icon": "diamond", "description": "Acesso a investimentos premium"},
        "exclusive_events": {"name": "Eventos Exclusivos", "icon": "ribbon", "description": "Convites para eventos especiais"},
    }
    
    active_perks = [perk_descriptions.get(p, {"name": p, "icon": "star", "description": ""}) for p in tier.get('perks', [])]
    
    return {
        "reputation": reputation,
        "tier": tier['tier'],
        "stars": tier['stars'],
        "color": tier['color'],
        "icon": tier['icon'],
        "progress_to_next": round(progress, 1),
        "next_tier": next_tier['tier'] if tier != next_tier else None,
        "active_perks": active_perks,
        "all_tiers": REPUTATION_TIERS,
        "history": rep_history,
    }
