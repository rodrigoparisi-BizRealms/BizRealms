"""BizRealms - AI Dynamic Events System
Generates personalized game events using GPT based on player state.
Events have choices with real consequences (money, XP, reputation).
Difficulty adapts to player growth rate.
"""

import os
import json
import uuid
import random
import logging
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

router = APIRouter()

from database import db
from utils import get_current_user, security

# ==================== EVENT CONFIGURATION ====================

EVENT_COOLDOWN_HOURS = 4  # Minimum hours between events
EVENT_EXPIRY_HOURS = 8    # Event expires after this time

EVENT_TYPES = {
    "opportunity": {"emoji": "💎", "color": "#4CAF50"},
    "crisis": {"emoji": "⚠️", "color": "#F44336"},
    "challenge": {"emoji": "🎯", "color": "#FF9800"},
    "luck": {"emoji": "🍀", "color": "#8BC34A"},
    "decision": {"emoji": "⚖️", "color": "#2196F3"},
    "market": {"emoji": "📊", "color": "#9C27B0"},
}

# ==================== FALLBACK EVENTS (offline/GPT failure) ====================

FALLBACK_EVENTS = {
    "low": [  # Level 1-5
        {
            "type": "opportunity",
            "title": "Investidor Anjo",
            "description": "Um investidor viu potencial em você e oferece um aporte inicial para seu primeiro negócio.",
            "choices": [
                {"id": "accept", "text": "Aceitar o investimento", "consequences": {"money": 3000, "xp": 50}},
                {"id": "decline", "text": "Recusar e crescer sozinho", "consequences": {"xp": 100}},
            ]
        },
        {
            "type": "luck",
            "title": "Achado na Rua",
            "description": "Você encontrou uma carteira com dinheiro e documentos. O dono é um empresário local.",
            "choices": [
                {"id": "return", "text": "Devolver a carteira", "consequences": {"xp": 80, "money": 1000}},
                {"id": "keep", "text": "Ficar com o dinheiro", "consequences": {"money": 2000, "xp": -20}},
            ]
        },
        {
            "type": "challenge",
            "title": "Trabalho Extra",
            "description": "Seu chefe oferece um projeto urgente no fim de semana. Paga bem, mas é cansativo.",
            "choices": [
                {"id": "accept", "text": "Aceitar o projeto", "consequences": {"money": 2500, "xp": 60}},
                {"id": "decline", "text": "Descansar no fim de semana", "consequences": {"xp": 30}},
            ]
        },
        {
            "type": "opportunity",
            "title": "Curso Gratuito",
            "description": "Uma universidade oferece bolsa integral para um curso de gestão empresarial.",
            "choices": [
                {"id": "enroll", "text": "Se inscrever no curso", "consequences": {"xp": 150, "money": -500}},
                {"id": "skip", "text": "Não tenho tempo agora", "consequences": {"money": 500}},
            ]
        },
    ],
    "mid": [  # Level 5-15
        {
            "type": "crisis",
            "title": "Funcionário Problemático",
            "description": "Um funcionário-chave está causando problemas e ameaça processar sua empresa.",
            "choices": [
                {"id": "fire", "text": "Demitir e pagar indenização", "consequences": {"money": -5000, "xp": 40}},
                {"id": "negotiate", "text": "Negociar acordo", "consequences": {"money": -2000, "xp": 80}},
                {"id": "ignore", "text": "Ignorar a situação", "consequences": {"money": -10000, "xp": -30}},
            ]
        },
        {
            "type": "market",
            "title": "Crise no Mercado",
            "description": "O mercado financeiro despencou 20%. Seus investimentos estão em queda livre.",
            "choices": [
                {"id": "sell", "text": "Vender tudo antes de cair mais", "consequences": {"money": -3000, "xp": 30}},
                {"id": "hold", "text": "Manter e esperar recuperação", "consequences": {"xp": 60}},
                {"id": "buy", "text": "Comprar mais na baixa!", "consequences": {"money": -5000, "xp": 120}},
            ]
        },
        {
            "type": "opportunity",
            "title": "Proposta de Sociedade",
            "description": "Um empresário bem-sucedido propõe sociedade em um novo negócio promissor.",
            "choices": [
                {"id": "accept", "text": "Aceitar a sociedade", "consequences": {"money": -10000, "xp": 150}},
                {"id": "counter", "text": "Contraproposta: maioria das ações", "consequences": {"money": -15000, "xp": 200}},
                {"id": "decline", "text": "Recusar e focar no próprio", "consequences": {"xp": 50}},
            ]
        },
        {
            "type": "decision",
            "title": "Fornecedor Faliu",
            "description": "Seu principal fornecedor declarou falência. Você precisa agir rápido.",
            "choices": [
                {"id": "new_supplier", "text": "Buscar novo fornecedor (mais caro)", "consequences": {"money": -8000, "xp": 60}},
                {"id": "produce", "text": "Produzir internamente", "consequences": {"money": -15000, "xp": 150}},
                {"id": "pause", "text": "Pausar operações temporariamente", "consequences": {"money": -3000, "xp": 20}},
            ]
        },
    ],
    "high": [  # Level 15+
        {
            "type": "crisis",
            "title": "Auditoria Fiscal",
            "description": "A Receita Federal iniciou uma auditoria em suas empresas. Irregularidades foram encontradas.",
            "choices": [
                {"id": "pay", "text": "Pagar multa e regularizar tudo", "consequences": {"money": -50000, "xp": 100}},
                {"id": "lawyer", "text": "Contratar advogado tributarista", "consequences": {"money": -20000, "xp": 150}},
                {"id": "negotiate", "text": "Negociar parcelamento", "consequences": {"money": -35000, "xp": 80}},
            ]
        },
        {
            "type": "opportunity",
            "title": "Aquisição Hostil",
            "description": "Uma multinacional quer comprar sua maior empresa por 3x o valor. Oferta irrecusável?",
            "choices": [
                {"id": "sell", "text": "Vender e lucrar alto", "consequences": {"money": 100000, "xp": 200}},
                {"id": "partial", "text": "Vender 49% e manter controle", "consequences": {"money": 40000, "xp": 300}},
                {"id": "refuse", "text": "Recusar e competir", "consequences": {"xp": 150, "money": -10000}},
            ]
        },
        {
            "type": "market",
            "title": "Nova Lei Tributária",
            "description": "O governo aprovou uma nova lei que aumenta impostos sobre grandes empresas em 15%.",
            "choices": [
                {"id": "adapt", "text": "Reestruturar empresas", "consequences": {"money": -30000, "xp": 200}},
                {"id": "lobby", "text": "Investir em lobby político", "consequences": {"money": -50000, "xp": 100}},
                {"id": "offshore", "text": "Mover operações para o exterior", "consequences": {"money": -80000, "xp": 250}},
            ]
        },
        {
            "type": "decision",
            "title": "Concorrência Agressiva",
            "description": "Um concorrente está roubando seus clientes com preços 30% menores. Suas receitas caíram.",
            "choices": [
                {"id": "price_war", "text": "Entrar na guerra de preços", "consequences": {"money": -40000, "xp": 80}},
                {"id": "innovate", "text": "Inovar e diferenciar o produto", "consequences": {"money": -20000, "xp": 250}},
                {"id": "acquire", "text": "Comprar o concorrente", "consequences": {"money": -100000, "xp": 400}},
            ]
        },
    ],
}

# ==================== GPT EVENT PROMPT ====================

EVENT_SYSTEM_PROMPT = """Você é o motor de eventos do jogo BizRealms, um simulador de negócios.
Gere UM evento dinâmico e personalizado baseado nos dados do jogador.

REGRAS:
1. O evento deve ser REALISTA e baseado no contexto empresarial brasileiro
2. Deve ter 2-3 escolhas com consequências DIFERENTES (positivas e negativas)
3. Consequências em dinheiro devem ser proporcionais ao patrimônio do jogador
4. Eventos devem ser SURPREENDENTES e quebrar a rotina do jogador
5. Inclua dilemas morais/éticos quando possível
6. Adapte a dificuldade ao nível do jogador

FORMATO DE RESPOSTA (JSON ESTRITO):
{
  "type": "opportunity|crisis|challenge|luck|decision|market",
  "title": "Título curto e impactante",
  "description": "Descrição de 2-3 frases sobre a situação",
  "choices": [
    {"id": "choice_1", "text": "Texto da escolha 1", "consequences": {"money": 5000, "xp": 50}},
    {"id": "choice_2", "text": "Texto da escolha 2", "consequences": {"money": -3000, "xp": 100}},
    {"id": "choice_3", "text": "Texto da escolha 3 (opcional)", "consequences": {"money": 0, "xp": 30}}
  ]
}

IMPORTANTE: Retorne APENAS o JSON, sem texto adicional."""


# ==================== ENDPOINTS ====================

@router.get("/events/active")
async def get_active_event(current_user: dict = Depends(get_current_user)):
    """Get the currently active event for the player, or null if none."""
    uid = current_user['id']
    now = datetime.utcnow()

    # Find active (non-expired, non-resolved) event
    event = await db.game_events.find_one({
        "user_id": uid,
        "resolved": False,
        "expires_at": {"$gt": now},
    })

    if event:
        event.pop('_id', None)
        return {"event": event, "has_event": True}

    # Check cooldown
    last_event = await db.game_events.find_one(
        {"user_id": uid},
        sort=[("created_at", -1)]
    )
    if last_event:
        last_time = last_event.get('created_at', now - timedelta(hours=24))
        if isinstance(last_time, str):
            last_time = datetime.fromisoformat(last_time.replace('Z', '+00:00'))
        if (now - last_time).total_seconds() < EVENT_COOLDOWN_HOURS * 3600:
            remaining = EVENT_COOLDOWN_HOURS * 3600 - (now - last_time).total_seconds()
            return {"event": None, "has_event": False, "cooldown_remaining": int(remaining)}

    return {"event": None, "has_event": False, "cooldown_remaining": 0}


@router.post("/events/generate")
async def generate_event(current_user: dict = Depends(get_current_user)):
    """Generate a new dynamic event based on player state."""
    uid = current_user['id']
    now = datetime.utcnow()

    # Check if there's already an active event
    existing = await db.game_events.find_one({
        "user_id": uid,
        "resolved": False,
        "expires_at": {"$gt": now},
    })
    if existing:
        existing.pop('_id', None)
        return {"event": existing, "generated": False, "message": "Evento ativo já existe"}

    # Check cooldown
    last_event = await db.game_events.find_one(
        {"user_id": uid},
        sort=[("created_at", -1)]
    )
    if last_event:
        last_time = last_event.get('created_at', now - timedelta(hours=24))
        if isinstance(last_time, str):
            last_time = datetime.fromisoformat(last_time.replace('Z', '+00:00'))
        if (now - last_time).total_seconds() < EVENT_COOLDOWN_HOURS * 3600:
            return {"event": None, "generated": False, "message": "Aguarde o cooldown"}

    # Get player state
    user = await db.users.find_one({"id": uid})
    level = user.get('level', 1)
    money = user.get('money', 0)

    companies = await db.companies.find({"owner_id": uid}).to_list(100)
    investments = await db.investments.find({"user_id": uid}).to_list(100)
    assets = await db.assets.find({"user_id": uid}).to_list(100)

    inv_value = sum(i.get('current_value', i.get('quantity', 0) * i.get('current_price', 0)) for i in investments)
    comp_revenue = sum(c.get('effective_revenue', c.get('monthly_revenue', 0)) for c in companies)
    comp_value = sum(c.get('purchase_price', 0) for c in companies)
    asset_value = sum(a.get('current_value', a.get('purchase_price', 0)) for a in assets)
    net_worth = money + inv_value + comp_value + asset_value

    # Determine difficulty tier
    if level <= 5:
        difficulty = "low"
    elif level <= 15:
        difficulty = "mid"
    else:
        difficulty = "high"

    # Try GPT generation first
    event_data = None
    ai_generated = False
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        llm_key = os.getenv('EMERGENT_LLM_KEY')
        if llm_key:
            player_context = f"""
DADOS DO JOGADOR:
- Nível: {level} | Dificuldade: {difficulty}
- Dinheiro em caixa: R$ {money:,.2f}
- Patrimônio líquido: R$ {net_worth:,.2f}
- Empresas: {len(companies)} (receita mensal: R$ {comp_revenue:,.2f})
- Investimentos: {len(investments)} (valor: R$ {inv_value:,.2f})
- Imóveis/Bens: {len(assets)} (valor: R$ {asset_value:,.2f})
- Educação: {len(user.get('education', []))} formações
- Certificações: {len(user.get('certifications', []))}

REGRAS DE VALORES:
- Consequências em dinheiro devem ser entre {int(net_worth * 0.01)} e {int(net_worth * 0.15)} (1-15% do patrimônio)
- Nível {difficulty}: {'eventos fáceis e generosos' if difficulty == 'low' else 'eventos moderados com dilemas' if difficulty == 'mid' else 'eventos complexos e desafiadores'}
- XP entre 30 e 300

Gere um evento SURPREENDENTE e ÚNICO para este jogador."""

            chat = LlmChat(
                api_key=llm_key,
                session_id=f"events-{uid}-{now.strftime('%Y%m%d%H%M')}",
                system_message=EVENT_SYSTEM_PROMPT,
            )
            chat.with_model("openai", "gpt-4.1-mini")

            msg = UserMessage(text=player_context)
            response = await chat.send_message(msg)

            # Parse JSON from response
            clean = response.strip()
            if clean.startswith('```'):
                clean = clean.split('\n', 1)[1] if '\n' in clean else clean[3:]
                clean = clean.rsplit('```', 1)[0]
            event_data = json.loads(clean)
            ai_generated = True
            logger.info(f"GPT event generated for user {uid}")
    except Exception as e:
        logger.warning(f"GPT event generation failed: {e}, using fallback")

    # Fallback to pre-defined events
    if not event_data:
        pool = FALLBACK_EVENTS.get(difficulty, FALLBACK_EVENTS['low'])
        event_data = random.choice(pool)
        # Scale money consequences to player's wealth
        scale = max(1, net_worth / 50000)
        for choice in event_data.get('choices', []):
            cons = choice.get('consequences', {})
            if 'money' in cons:
                cons['money'] = int(cons['money'] * scale)

    # Validate and store event
    event_type = event_data.get('type', 'opportunity')
    type_config = EVENT_TYPES.get(event_type, EVENT_TYPES['opportunity'])

    event = {
        "id": str(uuid.uuid4()),
        "user_id": uid,
        "type": event_type,
        "title": event_data.get('title', 'Evento'),
        "description": event_data.get('description', ''),
        "emoji": type_config['emoji'],
        "color": type_config['color'],
        "choices": event_data.get('choices', []),
        "difficulty": difficulty,
        "ai_generated": ai_generated,
        "resolved": False,
        "created_at": now,
        "expires_at": now + timedelta(hours=EVENT_EXPIRY_HOURS),
    }

    await db.game_events.insert_one(event)
    event.pop('_id', None)

    return {"event": event, "generated": True}


@router.post("/events/choose")
async def choose_event_option(request: dict, current_user: dict = Depends(get_current_user)):
    """Player makes a choice on an active event."""
    uid = current_user['id']
    event_id = request.get('event_id')
    choice_id = request.get('choice_id')

    if not event_id or not choice_id:
        raise HTTPException(status_code=400, detail="event_id e choice_id são obrigatórios")

    # Find the active event
    event = await db.game_events.find_one({
        "id": event_id,
        "user_id": uid,
        "resolved": False,
    })
    if not event:
        raise HTTPException(status_code=404, detail="Evento não encontrado ou já resolvido")

    # Find the chosen option
    chosen = None
    for c in event.get('choices', []):
        if c.get('id') == choice_id:
            chosen = c
            break

    if not chosen:
        raise HTTPException(status_code=400, detail="Escolha inválida")

    consequences = chosen.get('consequences', {})
    money_change = consequences.get('money', 0)
    xp_change = consequences.get('xp', 0)

    # Apply consequences
    update = {}
    if money_change != 0:
        update['money'] = money_change
    if xp_change != 0:
        update['experience_points'] = xp_change

    if update:
        # Ensure money doesn't go below 0
        user = await db.users.find_one({"id": uid})
        current_money = user.get('money', 0)
        if money_change < 0 and current_money + money_change < 0:
            money_change = -current_money  # Take only what they have
            update['money'] = money_change

        await db.users.update_one({"id": uid}, {"$inc": update})

    # Mark event as resolved
    await db.game_events.update_one(
        {"id": event_id},
        {"$set": {
            "resolved": True,
            "resolved_at": datetime.utcnow(),
            "chosen_option": choice_id,
            "applied_consequences": {"money": money_change, "xp": xp_change},
        }}
    )

    # Create notification
    await db.notifications.insert_one({
        "user_id": uid,
        "type": "event_result",
        "title": f"Resultado: {event.get('title', 'Evento')}",
        "message": f"Escolha: {chosen['text']}. {'💰' if money_change > 0 else '💸'} {'+' if money_change >= 0 else ''}{money_change:,} | {'⭐' if xp_change > 0 else '📉'} {'+' if xp_change >= 0 else ''}{xp_change} XP",
        "icon": "flag",
        "read": False,
        "created_at": datetime.utcnow(),
    })

    return {
        "success": True,
        "choice": chosen['text'],
        "consequences": {"money": money_change, "xp": xp_change},
        "message": f"{'Ganhou' if money_change > 0 else 'Perdeu'} R$ {abs(money_change):,} | {'+' if xp_change >= 0 else ''}{xp_change} XP",
    }


@router.get("/events/history")
async def get_event_history(current_user: dict = Depends(get_current_user)):
    """Get player's event history."""
    uid = current_user['id']
    events = await db.game_events.find(
        {"user_id": uid, "resolved": True}
    ).sort("resolved_at", -1).to_list(20)

    for e in events:
        e.pop('_id', None)

    return {"events": events, "count": len(events)}
