"""BizRealms - Life Phases & Crises System."""
import logging
import uuid
import random
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

router = APIRouter()

from database import db
from utils import get_current_user, calculate_level, security
from routes.investments import get_current_price

# ==================== PHASE DEFINITIONS ====================

PHASES = [
    {
        "id": "survival",
        "name": "Sobrevivência",
        "emoji": "🟢",
        "color": "#4CAF50",
        "icon": "shield-checkmark",
        "min_net_worth": 0,
        "max_net_worth": 50000,
        "description": "Você está começando. Foque em conseguir emprego, estudar e economizar.",
        "bonuses": {
            "xp_multiplier": 1.0,
            "income_bonus": 0,
            "company_slots": 1,
            "investment_bonus": 0,
        },
        "unlocks": ["Empregos básicos", "Educação fundamental", "Investimentos simples"],
        "tips": [
            "Arrume um emprego estável primeiro",
            "Invista em educação para subir de cargo",
            "Economize pelo menos 30% do salário",
        ],
        "crisis_frequency_hours": 168,  # 1 crisis per week max
        "crisis_severity": "low",
    },
    {
        "id": "growth",
        "name": "Crescimento",
        "emoji": "🔵",
        "color": "#2196F3",
        "icon": "trending-up",
        "min_net_worth": 50000,
        "max_net_worth": 500000,
        "description": "Hora de expandir! Abra empresas, diversifique investimentos.",
        "bonuses": {
            "xp_multiplier": 1.15,
            "income_bonus": 5,
            "company_slots": 3,
            "investment_bonus": 3,
        },
        "unlocks": ["Empresas médias", "Certificações avançadas", "Franquias", "Imóveis comerciais"],
        "tips": [
            "Abra sua primeira empresa",
            "Diversifique seus investimentos",
            "Faça certificações para bônus no ranking",
        ],
        "crisis_frequency_hours": 96,  # ~every 4 days
        "crisis_severity": "medium",
    },
    {
        "id": "empire",
        "name": "Império",
        "emoji": "🟣",
        "color": "#9C27B0",
        "icon": "business",
        "min_net_worth": 500000,
        "max_net_worth": 5000000,
        "description": "Você é um magnata! Gerencie seu império e domine mercados.",
        "bonuses": {
            "xp_multiplier": 1.3,
            "income_bonus": 12,
            "company_slots": 8,
            "investment_bonus": 7,
        },
        "unlocks": ["Empresas premium", "Franquias ilimitadas", "Imóveis de luxo", "Coaching IA avançado"],
        "tips": [
            "Expanda com franquias para renda passiva",
            "Invista em imóveis de alto valor",
            "Use o coaching IA para decisões estratégicas",
        ],
        "crisis_frequency_hours": 48,  # ~every 2 days
        "crisis_severity": "high",
    },
    {
        "id": "influence",
        "name": "Influência",
        "emoji": "🟠",
        "color": "#FF9800",
        "icon": "diamond",
        "min_net_worth": 5000000,
        "max_net_worth": float('inf'),
        "description": "Lendário! Você domina o mercado. Seu legado será eterno.",
        "bonuses": {
            "xp_multiplier": 1.5,
            "income_bonus": 20,
            "company_slots": 15,
            "investment_bonus": 12,
        },
        "unlocks": ["Tudo desbloqueado", "Bônus exclusivos", "Título de Lenda", "Eventos VIP"],
        "tips": [
            "Mantenha seu império diversificado",
            "Prepare-se para o sistema de Prestígio",
            "Domine todos os rankings",
        ],
        "crisis_frequency_hours": 24,  # daily crises possible
        "crisis_severity": "extreme",
    },
]

# ==================== CRISIS TEMPLATES ====================

CRISIS_TEMPLATES = {
    "low": [
        {
            "type": "tax_audit",
            "title": "Auditoria Fiscal",
            "emoji": "📋",
            "color": "#FF9800",
            "description": "A Receita Federal está investigando suas finanças. Pague uma multa ou arrisque uma penalidade maior.",
            "options": [
                {"id": "pay", "text": "Pagar multa imediatamente", "cost_pct": 2, "xp": 30, "risk": 0},
                {"id": "contest", "text": "Contestar a auditoria", "cost_pct": 0, "xp": 50, "risk": 60, "risk_cost_pct": 5},
            ],
        },
        {
            "type": "equipment_failure",
            "title": "Falha de Equipamento",
            "emoji": "🔧",
            "color": "#795548",
            "description": "Um equipamento essencial quebrou. Você precisa resolver rapidamente.",
            "options": [
                {"id": "repair", "text": "Consertar (mais barato)", "cost_pct": 1, "xp": 20, "risk": 0},
                {"id": "replace", "text": "Substituir por novo", "cost_pct": 3, "xp": 40, "risk": 0},
            ],
        },
        {
            "type": "employee_complaint",
            "title": "Reclamação Trabalhista",
            "emoji": "👷",
            "color": "#F44336",
            "description": "Um funcionário registrou uma queixa. Resolva antes que escale.",
            "options": [
                {"id": "settle", "text": "Acordo amigável", "cost_pct": 1.5, "xp": 25, "risk": 0},
                {"id": "ignore", "text": "Ignorar a queixa", "cost_pct": 0, "xp": 0, "risk": 70, "risk_cost_pct": 4},
            ],
        },
    ],
    "medium": [
        {
            "type": "lawsuit",
            "title": "Processo Judicial",
            "emoji": "⚖️",
            "color": "#F44336",
            "description": "Sua empresa está sendo processada por um concorrente. Prepare-se para gastar.",
            "options": [
                {"id": "settle", "text": "Fazer acordo judicial", "cost_pct": 5, "xp": 60, "risk": 0},
                {"id": "fight", "text": "Lutar no tribunal", "cost_pct": 3, "xp": 100, "risk": 50, "risk_cost_pct": 10},
            ],
        },
        {
            "type": "market_crash",
            "title": "Queda do Mercado",
            "emoji": "📉",
            "color": "#E91E63",
            "description": "O mercado despencou! Suas empresas estão perdendo valor rapidamente.",
            "options": [
                {"id": "hold", "text": "Manter e esperar recuperação", "cost_pct": 3, "xp": 50, "risk": 30, "risk_cost_pct": 6},
                {"id": "cut_losses", "text": "Cortar perdas imediatamente", "cost_pct": 5, "xp": 40, "risk": 0},
            ],
        },
        {
            "type": "employee_strike",
            "title": "Greve dos Funcionários",
            "emoji": "✊",
            "color": "#FF5722",
            "description": "Seus funcionários entraram em greve! A produção parou.",
            "options": [
                {"id": "negotiate", "text": "Negociar aumento salarial", "cost_pct": 4, "xp": 70, "risk": 0},
                {"id": "fire", "text": "Demitir e contratar novos", "cost_pct": 6, "xp": 30, "risk": 0},
                {"id": "wait", "text": "Esperar a greve acabar", "cost_pct": 2, "xp": 10, "risk": 40, "risk_cost_pct": 8},
            ],
        },
        {
            "type": "regulation_change",
            "title": "Nova Regulamentação",
            "emoji": "📜",
            "color": "#9C27B0",
            "description": "O governo mudou as regras do setor. Você precisa se adaptar.",
            "options": [
                {"id": "comply", "text": "Adaptar-se rapidamente", "cost_pct": 4, "xp": 80, "risk": 0},
                {"id": "lobby", "text": "Fazer lobby contra a lei", "cost_pct": 3, "xp": 50, "risk": 55, "risk_cost_pct": 7},
            ],
        },
    ],
    "high": [
        {
            "type": "hostile_takeover",
            "title": "Tentativa de Aquisição Hostil",
            "emoji": "🏴",
            "color": "#D32F2F",
            "description": "Um conglomerado está tentando comprar sua empresa à força!",
            "options": [
                {"id": "defend", "text": "Defesa agressiva (caro)", "cost_pct": 8, "xp": 150, "risk": 0},
                {"id": "negotiate", "text": "Negociar termos", "cost_pct": 5, "xp": 100, "risk": 30, "risk_cost_pct": 12},
                {"id": "surrender", "text": "Aceitar a oferta", "cost_pct": 0, "xp": 20, "risk": 0, "lose_company": True},
            ],
        },
        {
            "type": "scandal",
            "title": "Escândalo Corporativo",
            "emoji": "📰",
            "color": "#B71C1C",
            "description": "Um escândalo vazou na mídia! Sua reputação está em jogo.",
            "options": [
                {"id": "pr_campaign", "text": "Campanha de relações públicas", "cost_pct": 7, "xp": 120, "risk": 0},
                {"id": "deny", "text": "Negar tudo", "cost_pct": 1, "xp": 30, "risk": 70, "risk_cost_pct": 15},
            ],
        },
        {
            "type": "cyber_attack",
            "title": "Ataque Cibernético",
            "emoji": "🔒",
            "color": "#1A237E",
            "description": "Hackers invadiram seus sistemas! Dados sensíveis estão em risco.",
            "options": [
                {"id": "security_team", "text": "Contratar equipe de segurança", "cost_pct": 6, "xp": 130, "risk": 0},
                {"id": "pay_ransom", "text": "Pagar resgate", "cost_pct": 4, "xp": 20, "risk": 40, "risk_cost_pct": 10},
                {"id": "rebuild", "text": "Reconstruir do zero", "cost_pct": 10, "xp": 200, "risk": 0},
            ],
        },
    ],
    "extreme": [
        {
            "type": "economic_depression",
            "title": "Depressão Econômica",
            "emoji": "🌪️",
            "color": "#880E4F",
            "description": "Uma crise econômica global! Todos os setores estão em colapso.",
            "options": [
                {"id": "diversify", "text": "Diversificar urgentemente", "cost_pct": 8, "xp": 200, "risk": 20, "risk_cost_pct": 5},
                {"id": "hunker_down", "text": "Reduzir operações", "cost_pct": 5, "xp": 100, "risk": 0},
                {"id": "aggressive", "text": "Comprar concorrentes baratos", "cost_pct": 12, "xp": 300, "risk": 40, "risk_cost_pct": 8},
            ],
        },
        {
            "type": "government_seizure",
            "title": "Investigação Federal",
            "emoji": "🏛️",
            "color": "#311B92",
            "description": "O governo federal abriu uma investigação contra seu império!",
            "options": [
                {"id": "cooperate", "text": "Cooperar totalmente", "cost_pct": 10, "xp": 250, "risk": 0},
                {"id": "legal_team", "text": "Contratar mega advogados", "cost_pct": 15, "xp": 150, "risk": 30, "risk_cost_pct": 20},
            ],
        },
    ],
}


# ==================== HELPER: NET WORTH CALCULATION ====================

async def calculate_net_worth_simple(user_id: str, user: dict) -> float:
    """Calculate user net worth for phase determination."""
    cash = user.get('money', 0)

    investment_value = 0
    holdings = await db.user_holdings.find({"user_id": user_id}).to_list(200)
    for h in holdings:
        asset = await db.investment_assets.find_one({"id": h['asset_id']})
        if asset:
            investment_value += h['quantity'] * get_current_price(asset)

    companies_value = 0
    companies = await db.user_companies.find({"user_id": user_id}).to_list(200)
    for c in companies:
        companies_value += c.get('purchase_price', 0)

    assets_value = 0
    assets = await db.user_assets.find({"user_id": user_id}).to_list(200)
    for a in assets:
        purchase_price = a.get('purchase_price', 0)
        rate = a.get('appreciation_rate', 0) / 100
        purchased_at = a.get('purchased_at', datetime.utcnow())
        if isinstance(purchased_at, str):
            from dateutil.parser import parse
            purchased_at = parse(purchased_at)
        days = (datetime.utcnow() - purchased_at).days
        assets_value += max(0, purchase_price * (1 + rate * days / 365))

    return cash + investment_value + companies_value + assets_value


def get_phase_for_net_worth(net_worth: float) -> dict:
    """Get the phase definition for a given net worth."""
    for phase in reversed(PHASES):
        if net_worth >= phase['min_net_worth']:
            return phase
    return PHASES[0]


# ==================== PHASE ENDPOINTS ====================

@router.get("/phases/current")
async def get_current_phase(current_user: dict = Depends(get_current_user)):
    """Get the player's current life phase with progress and bonuses."""
    uid = current_user['id']
    net_worth = await calculate_net_worth_simple(uid, current_user)
    phase = get_phase_for_net_worth(net_worth)

    # Calculate progress to next phase
    phase_idx = next(i for i, p in enumerate(PHASES) if p['id'] == phase['id'])
    if phase_idx < len(PHASES) - 1:
        next_phase = PHASES[phase_idx + 1]
        progress = (net_worth - phase['min_net_worth']) / (next_phase['min_net_worth'] - phase['min_net_worth'])
        progress = min(max(progress, 0), 1)
        remaining = next_phase['min_net_worth'] - net_worth
    else:
        next_phase = None
        progress = 1.0
        remaining = 0

    # Count companies for crisis scaling
    company_count = await db.user_companies.count_documents({"user_id": uid})

    # Save phase to user record for quick access
    await db.users.update_one(
        {"id": uid},
        {"$set": {"current_phase": phase['id'], "net_worth_cached": round(net_worth, 2)}}
    )

    return {
        "phase": {
            "id": phase['id'],
            "name": phase['name'],
            "emoji": phase['emoji'],
            "color": phase['color'],
            "icon": phase['icon'],
            "description": phase['description'],
            "bonuses": phase['bonuses'],
            "unlocks": phase['unlocks'],
            "tips": phase['tips'],
        },
        "progress": round(progress, 4),
        "net_worth": round(net_worth, 2),
        "next_phase": {
            "id": next_phase['id'],
            "name": next_phase['name'],
            "emoji": next_phase['emoji'],
            "color": next_phase['color'],
            "min_net_worth": next_phase['min_net_worth'],
            "remaining": round(remaining, 2),
        } if next_phase else None,
        "phase_index": phase_idx,
        "total_phases": len(PHASES),
        "company_count": company_count,
    }


@router.get("/phases/all")
async def get_all_phases(current_user: dict = Depends(get_current_user)):
    """Get all phase definitions."""
    uid = current_user['id']
    net_worth = await calculate_net_worth_simple(uid, current_user)
    current_phase = get_phase_for_net_worth(net_worth)

    phases_out = []
    for p in PHASES:
        phases_out.append({
            "id": p['id'],
            "name": p['name'],
            "emoji": p['emoji'],
            "color": p['color'],
            "icon": p['icon'],
            "description": p['description'],
            "bonuses": p['bonuses'],
            "unlocks": p['unlocks'],
            "min_net_worth": p['min_net_worth'],
            "max_net_worth": p['max_net_worth'] if p['max_net_worth'] != float('inf') else None,
            "is_current": p['id'] == current_phase['id'],
            "is_unlocked": net_worth >= p['min_net_worth'],
        })
    return {"phases": phases_out, "current_net_worth": round(net_worth, 2)}


# ==================== CRISIS ENDPOINTS ====================

@router.get("/crises/active")
async def get_active_crises(current_user: dict = Depends(get_current_user)):
    """Check for active crises that need resolution."""
    uid = current_user['id']
    active = await db.game_crises.find({
        "user_id": uid,
        "status": "active",
    }).to_list(10)

    crises = []
    for c in active:
        c.pop('_id', None)
        # Check expiry — auto-resolve with penalty if expired
        expires_at = c.get('expires_at')
        if expires_at and datetime.utcnow() > expires_at:
            penalty_pct = c.get('auto_penalty_pct', 3)
            user = await db.users.find_one({"id": uid})
            penalty = max(100, user.get('money', 0) * penalty_pct / 100)
            await db.users.update_one({"id": uid}, {"$inc": {"money": -penalty}})
            await db.game_crises.update_one(
                {"id": c['id']},
                {"$set": {
                    "status": "expired",
                    "resolved_at": datetime.utcnow(),
                    "auto_penalty": round(penalty, 2),
                }}
            )
            c['status'] = 'expired'
            c['auto_penalty'] = round(penalty, 2)
        crises.append(c)

    return {"crises": crises, "count": len([c for c in crises if c['status'] == 'active'])}


@router.post("/crises/check")
async def check_and_generate_crisis(current_user: dict = Depends(get_current_user)):
    """Check if a new crisis should spawn based on phase and company count."""
    uid = current_user['id']

    # Don't generate if there's already an active crisis
    active = await db.game_crises.count_documents({"user_id": uid, "status": "active"})
    if active > 0:
        return {"generated": False, "reason": "Já existe uma crise ativa", "active_count": active}

    # Check cooldown
    last_crisis = await db.game_crises.find_one(
        {"user_id": uid},
        sort=[("created_at", -1)]
    )

    net_worth = await calculate_net_worth_simple(uid, current_user)
    phase = get_phase_for_net_worth(net_worth)
    cooldown_hours = phase.get('crisis_frequency_hours', 168)

    if last_crisis:
        created = last_crisis.get('created_at', datetime.utcnow())
        if isinstance(created, str):
            created = datetime.fromisoformat(created.replace('Z', '+00:00'))
        elapsed = (datetime.utcnow() - created).total_seconds() / 3600
        if elapsed < cooldown_hours:
            remaining = cooldown_hours - elapsed
            return {
                "generated": False,
                "reason": "Cooldown ativo",
                "cooldown_remaining_hours": round(remaining, 1),
            }

    # Company count affects probability
    company_count = await db.user_companies.count_documents({"user_id": uid})
    base_prob = 0.3 + (company_count * 0.05)  # More companies = higher chance
    base_prob = min(base_prob, 0.9)

    if random.random() > base_prob:
        return {"generated": False, "reason": "Sem crise desta vez", "probability": round(base_prob, 2)}

    # Generate crisis
    severity = phase.get('crisis_severity', 'low')
    templates = CRISIS_TEMPLATES.get(severity, CRISIS_TEMPLATES['low'])
    template = random.choice(templates)

    crisis_id = str(uuid.uuid4())[:8]
    crisis = {
        "id": crisis_id,
        "user_id": uid,
        "type": template['type'],
        "title": template['title'],
        "emoji": template['emoji'],
        "color": template['color'],
        "description": template['description'],
        "severity": severity,
        "phase": phase['id'],
        "options": template['options'],
        "status": "active",
        "created_at": datetime.utcnow(),
        "expires_at": datetime.utcnow() + timedelta(hours=24),
        "auto_penalty_pct": 5,
    }

    await db.game_crises.insert_one(crisis)
    crisis.pop('_id', None)

    # Create notification
    await db.notifications.insert_one({
        "id": str(uuid.uuid4())[:8],
        "user_id": uid,
        "type": "crisis",
        "title": f"{template['emoji']} CRISE: {template['title']}",
        "message": template['description'],
        "read": False,
        "created_at": datetime.utcnow(),
    })

    logger.info(f"Crisis generated for user {uid}: {template['type']} ({severity})")

    return {"generated": True, "crisis": crisis}


@router.post("/crises/resolve")
async def resolve_crisis(data: dict, current_user: dict = Depends(get_current_user)):
    """Resolve a crisis by choosing an option."""
    uid = current_user['id']
    crisis_id = data.get('crisis_id')
    option_id = data.get('option_id')

    if not crisis_id or not option_id:
        raise HTTPException(status_code=400, detail="crisis_id e option_id são obrigatórios")

    crisis = await db.game_crises.find_one({"id": crisis_id, "user_id": uid, "status": "active"})
    if not crisis:
        raise HTTPException(status_code=404, detail="Crise não encontrada ou já resolvida")

    # Find chosen option
    chosen = None
    for opt in crisis.get('options', []):
        if opt.get('id') == option_id:
            chosen = opt
            break

    if not chosen:
        raise HTTPException(status_code=400, detail="Opção inválida")

    user = await db.users.find_one({"id": uid})
    current_money = user.get('money', 0)

    # Calculate cost
    cost_pct = chosen.get('cost_pct', 0)
    base_cost = max(100, current_money * cost_pct / 100)

    # Check risk factor
    risk = chosen.get('risk', 0)
    risk_triggered = False
    extra_cost = 0

    if risk > 0:
        if random.randint(1, 100) <= risk:
            risk_triggered = True
            risk_cost_pct = chosen.get('risk_cost_pct', cost_pct * 2)
            extra_cost = max(50, current_money * risk_cost_pct / 100)

    total_cost = round(base_cost + extra_cost, 2)
    xp_gained = chosen.get('xp', 0)

    # Apply consequences
    new_exp = user.get('experience_points', 0) + xp_gained
    new_level = calculate_level(new_exp)

    update_ops = {
        "$inc": {"money": -total_cost},
        "$set": {"experience_points": new_exp, "level": new_level},
    }
    await db.users.update_one({"id": uid}, update_ops)

    # Handle special effects
    lost_company = None
    if chosen.get('lose_company') and not risk_triggered:
        # Lose a random company
        company = await db.user_companies.find_one({"user_id": uid})
        if company:
            lost_company = company.get('name', 'Empresa')
            await db.user_companies.delete_one({"_id": company['_id']})

    # Mark crisis resolved
    await db.game_crises.update_one(
        {"id": crisis_id},
        {"$set": {
            "status": "resolved",
            "resolved_at": datetime.utcnow(),
            "chosen_option": option_id,
            "cost_applied": total_cost,
            "xp_gained": xp_gained,
            "risk_triggered": risk_triggered,
            "extra_cost": extra_cost,
            "lost_company": lost_company,
        }}
    )

    # Build result message
    if risk_triggered:
        message = f"Risco se concretizou! Custo adicional de {extra_cost:.0f}. Total: -{total_cost:.0f}"
    else:
        message = f"Crise resolvida! Custo: -{total_cost:.0f}"

    if lost_company:
        message += f" Você perdeu: {lost_company}"

    # Create notification
    await db.notifications.insert_one({
        "id": str(uuid.uuid4())[:8],
        "user_id": uid,
        "type": "crisis_resolved",
        "title": f"✅ Crise Resolvida: {crisis.get('title', 'Crise')}",
        "message": message,
        "read": False,
        "created_at": datetime.utcnow(),
    })

    return {
        "success": True,
        "option_chosen": chosen.get('text', ''),
        "cost": round(base_cost, 2),
        "risk_triggered": risk_triggered,
        "extra_cost": round(extra_cost, 2),
        "total_cost": total_cost,
        "xp_gained": xp_gained,
        "lost_company": lost_company,
        "message": message,
        "new_money": round(current_money - total_cost, 2),
    }


@router.get("/crises/history")
async def get_crises_history(current_user: dict = Depends(get_current_user)):
    """Get history of resolved crises."""
    uid = current_user['id']
    crises = await db.game_crises.find(
        {"user_id": uid, "status": {"$in": ["resolved", "expired"]}},
    ).sort("resolved_at", -1).to_list(50)

    for c in crises:
        c.pop('_id', None)

    return {"crises": crises, "count": len(crises)}
