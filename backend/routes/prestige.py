"""BizRealms - Prestige System."""
import logging
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

router = APIRouter()

from database import db
from utils import get_current_user, calculate_level, security
from routes.phases import calculate_net_worth_simple

# ==================== PRESTIGE TIERS ====================

PRESTIGE_TIERS = [
    {"level": 0, "name": "Novato", "emoji": "⚪", "color": "#9E9E9E", "min_points": 0},
    {"level": 1, "name": "Bronze", "emoji": "🥉", "color": "#CD7F32", "min_points": 100},
    {"level": 2, "name": "Prata", "emoji": "🥈", "color": "#C0C0C0", "min_points": 500},
    {"level": 3, "name": "Ouro", "emoji": "🥇", "color": "#FFD700", "min_points": 1500},
    {"level": 4, "name": "Diamante", "emoji": "💎", "color": "#00BCD4", "min_points": 5000},
    {"level": 5, "name": "Lenda", "emoji": "👑", "color": "#FF6F00", "min_points": 15000},
]

# ==================== PRESTIGE PERKS ====================

PRESTIGE_PERKS = [
    {
        "id": "starting_money_1",
        "name": "Capital Inicial I",
        "description": "Comece com +$ 500 (total $ 1.500)",
        "emoji": "💰",
        "cost": 50,
        "category": "money",
        "effect": {"starting_money_bonus": 500},
        "tier_required": 0,
        "max_level": 1,
    },
    {
        "id": "starting_money_2",
        "name": "Capital Inicial II",
        "description": "Comece com +$ 2.000 (total $ 3.000)",
        "emoji": "💰",
        "cost": 200,
        "category": "money",
        "effect": {"starting_money_bonus": 2000},
        "tier_required": 1,
        "max_level": 1,
        "requires": "starting_money_1",
    },
    {
        "id": "starting_money_3",
        "name": "Capital Inicial III",
        "description": "Comece com +$ 5.000 (total $ 6.000)",
        "emoji": "💰",
        "cost": 800,
        "category": "money",
        "effect": {"starting_money_bonus": 5000},
        "tier_required": 2,
        "max_level": 1,
        "requires": "starting_money_2",
    },
    {
        "id": "xp_boost_1",
        "name": "Experiência I",
        "description": "+10% XP ganho em todas as atividades",
        "emoji": "⚡",
        "cost": 75,
        "category": "xp",
        "effect": {"xp_multiplier": 1.10},
        "tier_required": 0,
        "max_level": 1,
    },
    {
        "id": "xp_boost_2",
        "name": "Experiência II",
        "description": "+25% XP ganho em todas as atividades",
        "emoji": "⚡",
        "cost": 300,
        "category": "xp",
        "effect": {"xp_multiplier": 1.25},
        "tier_required": 1,
        "max_level": 1,
        "requires": "xp_boost_1",
    },
    {
        "id": "xp_boost_3",
        "name": "Experiência III",
        "description": "+50% XP ganho em todas as atividades",
        "emoji": "⚡",
        "cost": 1000,
        "category": "xp",
        "effect": {"xp_multiplier": 1.50},
        "tier_required": 3,
        "max_level": 1,
        "requires": "xp_boost_2",
    },
    {
        "id": "company_slot",
        "name": "Empresário Nato",
        "description": "+2 slots de empresa desde o início",
        "emoji": "🏢",
        "cost": 150,
        "category": "companies",
        "effect": {"extra_company_slots": 2},
        "tier_required": 1,
        "max_level": 1,
    },
    {
        "id": "crisis_shield",
        "name": "Escudo de Crises",
        "description": "Crises custam 25% menos para resolver",
        "emoji": "🛡️",
        "cost": 250,
        "category": "defense",
        "effect": {"crisis_discount": 0.25},
        "tier_required": 1,
        "max_level": 1,
    },
    {
        "id": "event_cooldown",
        "name": "Sorte Acelerada",
        "description": "Eventos dinâmicos recarregam 50% mais rápido",
        "emoji": "🎯",
        "cost": 200,
        "category": "events",
        "effect": {"event_cooldown_reduction": 0.50},
        "tier_required": 1,
        "max_level": 1,
    },
    {
        "id": "investment_bonus",
        "name": "Olho de Investidor",
        "description": "+5% retorno em todos os investimentos",
        "emoji": "📈",
        "cost": 400,
        "category": "investments",
        "effect": {"investment_bonus": 0.05},
        "tier_required": 2,
        "max_level": 1,
    },
    {
        "id": "salary_boost",
        "name": "Negociador Nato",
        "description": "+15% salário em todos os empregos",
        "emoji": "💼",
        "cost": 350,
        "category": "jobs",
        "effect": {"salary_bonus": 0.15},
        "tier_required": 2,
        "max_level": 1,
    },
    {
        "id": "vip_status",
        "name": "Status VIP",
        "description": "Badge exclusivo + bônus de 10% no ranking",
        "emoji": "👑",
        "cost": 2000,
        "category": "status",
        "effect": {"ranking_bonus": 0.10, "vip_badge": True},
        "tier_required": 3,
        "max_level": 1,
    },
]


def get_prestige_tier(total_points: int) -> dict:
    """Get prestige tier for given total accumulated points."""
    tier = PRESTIGE_TIERS[0]
    for t in PRESTIGE_TIERS:
        if total_points >= t['min_points']:
            tier = t
    return tier


def calculate_prestige_points(net_worth: float) -> int:
    """Calculate prestige points earned from a reset based on net worth."""
    if net_worth < 10000:
        return 0
    if net_worth < 50000:
        return int(net_worth / 500)
    if net_worth < 500000:
        return int(100 + (net_worth - 50000) / 300)
    if net_worth < 5000000:
        return int(1600 + (net_worth - 500000) / 200)
    return int(24100 + (net_worth - 5000000) / 150)


# ==================== ENDPOINTS ====================

@router.get("/prestige/status")
async def get_prestige_status(current_user: dict = Depends(get_current_user)):
    """Get player's prestige status, points, tier, and active perks."""
    uid = current_user['id']

    prestige = await db.prestige.find_one({"user_id": uid})
    if not prestige:
        prestige = {
            "user_id": uid,
            "total_points_earned": 0,
            "available_points": 0,
            "resets_count": 0,
            "active_perks": [],
            "created_at": datetime.utcnow(),
        }
        await db.prestige.insert_one(prestige)

    total_earned = prestige.get('total_points_earned', 0)
    available = prestige.get('available_points', 0)
    active_perks = prestige.get('active_perks', [])
    resets = prestige.get('resets_count', 0)
    tier = get_prestige_tier(total_earned)

    # Calculate what they'd earn if they reset now
    net_worth = await calculate_net_worth_simple(uid, current_user)
    potential_points = calculate_prestige_points(net_worth)

    # Next tier
    current_tier_idx = next(i for i, t in enumerate(PRESTIGE_TIERS) if t['level'] == tier['level'])
    next_tier = PRESTIGE_TIERS[current_tier_idx + 1] if current_tier_idx < len(PRESTIGE_TIERS) - 1 else None

    return {
        "tier": tier,
        "total_points_earned": total_earned,
        "available_points": available,
        "resets_count": resets,
        "active_perks": active_perks,
        "potential_points": potential_points,
        "current_net_worth": round(net_worth, 2),
        "next_tier": next_tier,
        "perk_count": len(active_perks),
    }


@router.get("/prestige/perks")
async def get_prestige_perks(current_user: dict = Depends(get_current_user)):
    """Get all available perks with player's purchase status."""
    uid = current_user['id']

    prestige = await db.prestige.find_one({"user_id": uid})
    active_perks = prestige.get('active_perks', []) if prestige else []
    total_earned = prestige.get('total_points_earned', 0) if prestige else 0
    available = prestige.get('available_points', 0) if prestige else 0
    tier = get_prestige_tier(total_earned)

    perks_out = []
    for perk in PRESTIGE_PERKS:
        owned = perk['id'] in active_perks
        can_afford = available >= perk['cost']
        tier_unlocked = tier['level'] >= perk.get('tier_required', 0)
        prerequisite_met = True
        if perk.get('requires'):
            prerequisite_met = perk['requires'] in active_perks

        perks_out.append({
            **perk,
            "owned": owned,
            "can_afford": can_afford,
            "tier_unlocked": tier_unlocked,
            "prerequisite_met": prerequisite_met,
            "available": can_afford and tier_unlocked and prerequisite_met and not owned,
        })

    return {
        "perks": perks_out,
        "available_points": available,
        "tier": tier,
    }


@router.post("/prestige/buy-perk")
async def buy_prestige_perk(data: dict, current_user: dict = Depends(get_current_user)):
    """Purchase a prestige perk with prestige points."""
    uid = current_user['id']
    perk_id = data.get('perk_id')

    if not perk_id:
        raise HTTPException(status_code=400, detail="perk_id é obrigatório")

    perk = next((p for p in PRESTIGE_PERKS if p['id'] == perk_id), None)
    if not perk:
        raise HTTPException(status_code=404, detail="Perk não encontrado")

    prestige = await db.prestige.find_one({"user_id": uid})
    if not prestige:
        raise HTTPException(status_code=400, detail="Nenhum dado de prestígio encontrado")

    active_perks = prestige.get('active_perks', [])
    available = prestige.get('available_points', 0)
    total_earned = prestige.get('total_points_earned', 0)
    tier = get_prestige_tier(total_earned)

    if perk_id in active_perks:
        raise HTTPException(status_code=400, detail="Perk já comprado")
    if available < perk['cost']:
        raise HTTPException(status_code=400, detail=f"Pontos insuficientes. Precisa: {perk['cost']}, Tem: {available}")
    if tier['level'] < perk.get('tier_required', 0):
        raise HTTPException(status_code=400, detail="Tier de prestígio insuficiente")
    if perk.get('requires') and perk['requires'] not in active_perks:
        raise HTTPException(status_code=400, detail="Pré-requisito não atendido")

    # Buy perk
    await db.prestige.update_one(
        {"user_id": uid},
        {
            "$inc": {"available_points": -perk['cost']},
            "$push": {"active_perks": perk_id},
        }
    )

    logger.info(f"User {uid} bought prestige perk: {perk_id} for {perk['cost']} points")

    return {
        "success": True,
        "perk": perk,
        "remaining_points": available - perk['cost'],
        "message": f"Perk '{perk['name']}' ativado com sucesso!",
    }


@router.post("/prestige/reset")
async def prestige_reset(current_user: dict = Depends(get_current_user)):
    """Perform a prestige reset: earn points based on net worth, reset game data, keep perks."""
    uid = current_user['id']

    net_worth = await calculate_net_worth_simple(uid, current_user)
    points_earned = calculate_prestige_points(net_worth)

    if points_earned <= 0:
        raise HTTPException(
            status_code=400,
            detail="Patrimônio insuficiente para ganhar pontos de prestígio. Mínimo: $ 10.000"
        )

    # Get or create prestige record
    prestige = await db.prestige.find_one({"user_id": uid})
    if not prestige:
        prestige = {
            "user_id": uid,
            "total_points_earned": 0,
            "available_points": 0,
            "resets_count": 0,
            "active_perks": [],
            "created_at": datetime.utcnow(),
        }
        await db.prestige.insert_one(prestige)

    active_perks = prestige.get('active_perks', [])
    old_total = prestige.get('total_points_earned', 0)
    new_total = old_total + points_earned
    new_available = prestige.get('available_points', 0) + points_earned
    resets = prestige.get('resets_count', 0) + 1

    # Calculate perk bonuses for new start
    starting_money = 1000
    for perk_id in active_perks:
        perk = next((p for p in PRESTIGE_PERKS if p['id'] == perk_id), None)
        if perk and 'starting_money_bonus' in perk.get('effect', {}):
            starting_money = 1000 + perk['effect']['starting_money_bonus']

    # Update prestige
    await db.prestige.update_one(
        {"user_id": uid},
        {"$set": {
            "total_points_earned": new_total,
            "available_points": new_available,
            "resets_count": resets,
            "last_reset_at": datetime.utcnow(),
            "last_reset_net_worth": round(net_worth, 2),
            "last_reset_points": points_earned,
        }}
    )

    # Reset game data (keep auth, keep prestige)
    await db.users.update_one(
        {"id": uid},
        {"$set": {
            "money": starting_money,
            "level": 1,
            "experience_points": 0,
            "education": [],
            "certifications": [],
            "work_experience": [],
            "skills": {},
            "background": "",
            "dream": "",
            "daily_offers_used": 0,
            "last_offer_reset": None,
            "ads_watched_today": 0,
            "current_phase": "survival",
            "prestige_level": get_prestige_tier(new_total)['level'],
        }}
    )

    # Delete game data
    await db.user_companies.delete_many({"user_id": uid})
    await db.user_assets.delete_many({"user_id": uid})
    await db.user_investments.delete_many({"user_id": uid})
    await db.user_holdings.delete_many({"user_id": uid})
    await db.company_offers.delete_many({"user_id": uid})
    await db.asset_offers.delete_many({"user_id": uid})
    await db.user_loans.delete_many({"user_id": uid})
    await db.user_credit_cards.delete_many({"user_id": uid})
    await db.notifications.delete_many({"user_id": uid})
    await db.achievements.delete_many({"user_id": uid})
    await db.game_events.delete_many({"user_id": uid})
    await db.game_crises.delete_many({"user_id": uid})

    # Add notification
    await db.notifications.insert_one({
        "id": str(uuid.uuid4())[:8],
        "user_id": uid,
        "type": "prestige",
        "title": f"🏆 Prestígio #{resets}!",
        "message": f"Você ganhou {points_earned} pontos! Total: {new_total}. Patrimônio anterior: $ {net_worth:,.2f}",
        "read": False,
        "created_at": datetime.utcnow(),
    })

    old_tier = get_prestige_tier(old_total)
    new_tier = get_prestige_tier(new_total)

    logger.info(f"User {uid} prestige reset #{resets}: +{points_earned} pts (total: {new_total}), NW was {net_worth:.2f}")

    return {
        "success": True,
        "points_earned": points_earned,
        "total_points": new_total,
        "available_points": new_available,
        "resets_count": resets,
        "new_tier": new_tier,
        "tier_up": new_tier['level'] > old_tier['level'],
        "starting_money": starting_money,
        "active_perks": active_perks,
        "message": f"Prestígio #{resets}! +{points_earned} pontos de prestígio ganhos.",
    }
