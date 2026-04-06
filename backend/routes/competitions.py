"""BizRealms - Weekly Competitions System."""
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

# ==================== COMPETITION TEMPLATES ====================

COMPETITION_TEMPLATES = [
    {
        "type": "profit_king",
        "title": "Rei do Lucro",
        "emoji": "💰",
        "color": "#4CAF50",
        "description": "Quem acumular mais dinheiro durante a semana vence!",
        "metric": "money_gained",
        "metric_label": "Dinheiro ganho",
        "rewards": [
            {"position": 1, "money": 5000, "xp": 500, "label": "1o Lugar"},
            {"position": 2, "money": 2500, "xp": 300, "label": "2o Lugar"},
            {"position": 3, "money": 1000, "xp": 150, "label": "3o Lugar"},
        ],
    },
    {
        "type": "company_mogul",
        "title": "Magnata das Empresas",
        "emoji": "🏢",
        "color": "#2196F3",
        "description": "Quem abrir/comprar mais empresas durante a semana vence!",
        "metric": "companies_acquired",
        "metric_label": "Empresas adquiridas",
        "rewards": [
            {"position": 1, "money": 4000, "xp": 450, "label": "1o Lugar"},
            {"position": 2, "money": 2000, "xp": 250, "label": "2o Lugar"},
            {"position": 3, "money": 800, "xp": 100, "label": "3o Lugar"},
        ],
    },
    {
        "type": "investor_pro",
        "title": "Investidor Pro",
        "emoji": "📈",
        "color": "#9C27B0",
        "description": "Quem tiver o maior retorno em investimentos na semana vence!",
        "metric": "investment_profit",
        "metric_label": "Lucro em investimentos",
        "rewards": [
            {"position": 1, "money": 4500, "xp": 500, "label": "1o Lugar"},
            {"position": 2, "money": 2200, "xp": 280, "label": "2o Lugar"},
            {"position": 3, "money": 900, "xp": 120, "label": "3o Lugar"},
        ],
    },
    {
        "type": "xp_grinder",
        "title": "Mestre da Experiência",
        "emoji": "⚡",
        "color": "#FF9800",
        "description": "Quem ganhar mais XP durante a semana vence!",
        "metric": "xp_gained",
        "metric_label": "XP ganho",
        "rewards": [
            {"position": 1, "money": 3500, "xp": 600, "label": "1o Lugar"},
            {"position": 2, "money": 1800, "xp": 350, "label": "2o Lugar"},
            {"position": 3, "money": 700, "xp": 150, "label": "3o Lugar"},
        ],
    },
    {
        "type": "crisis_survivor",
        "title": "Sobrevivente de Crises",
        "emoji": "🛡️",
        "color": "#F44336",
        "description": "Quem resolver mais crises durante a semana vence!",
        "metric": "crises_resolved",
        "metric_label": "Crises resolvidas",
        "rewards": [
            {"position": 1, "money": 3000, "xp": 400, "label": "1o Lugar"},
            {"position": 2, "money": 1500, "xp": 200, "label": "2o Lugar"},
            {"position": 3, "money": 600, "xp": 100, "label": "3o Lugar"},
        ],
    },
    {
        "type": "net_worth_growth",
        "title": "Crescimento Explosivo",
        "emoji": "🚀",
        "color": "#E91E63",
        "description": "Quem aumentar mais o patrimônio líquido durante a semana!",
        "metric": "net_worth_growth",
        "metric_label": "Crescimento do patrimônio",
        "rewards": [
            {"position": 1, "money": 6000, "xp": 600, "label": "1o Lugar"},
            {"position": 2, "money": 3000, "xp": 350, "label": "2o Lugar"},
            {"position": 3, "money": 1200, "xp": 150, "label": "3o Lugar"},
        ],
    },
]


def get_week_bounds():
    """Get start and end of current week (Monday 00:00 to Sunday 23:59)."""
    now = datetime.utcnow()
    start = now - timedelta(days=now.weekday(), hours=now.hour, minutes=now.minute, seconds=now.second)
    start = start.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=7) - timedelta(seconds=1)
    return start, end


async def ensure_weekly_competition():
    """Create competition for current week if none exists."""
    week_start, week_end = get_week_bounds()

    existing = await db.competitions.find_one({
        "week_start": {"$gte": week_start},
        "status": {"$in": ["active", "finished"]},
    })

    if existing:
        return existing

    # Pick 2 random templates for this week
    selected = random.sample(COMPETITION_TEMPLATES, min(2, len(COMPETITION_TEMPLATES)))

    competitions = []
    for template in selected:
        comp_id = str(uuid.uuid4())[:8]
        comp = {
            "id": comp_id,
            "type": template['type'],
            "title": template['title'],
            "emoji": template['emoji'],
            "color": template['color'],
            "description": template['description'],
            "metric": template['metric'],
            "metric_label": template['metric_label'],
            "rewards": template['rewards'],
            "week_start": week_start,
            "week_end": week_end,
            "status": "active",
            "participants": [],
            "created_at": datetime.utcnow(),
        }
        await db.competitions.insert_one(comp)
        comp.pop('_id', None)
        competitions.append(comp)

    return competitions[0] if competitions else None


async def get_participant_score(user_id: str, metric: str, week_start: datetime) -> float:
    """Calculate a participant's score for a competition metric."""
    score = 0.0

    if metric == "money_gained":
        # Sum of money earned from jobs, companies, etc. this week
        user = await db.users.find_one({"id": user_id})
        score = user.get('money', 0)  # Simplified: use current balance as proxy

    elif metric == "companies_acquired":
        count = await db.user_companies.count_documents({
            "user_id": user_id,
            "purchased_at": {"$gte": week_start},
        })
        score = float(count)

    elif metric == "investment_profit":
        from routes.investments import get_current_price
        holdings = await db.user_holdings.find({"user_id": user_id}).to_list(200)
        for h in holdings:
            asset = await db.investment_assets.find_one({"id": h['asset_id']})
            if asset:
                current = get_current_price(asset)
                avg_cost = h.get('avg_price', current)
                score += (current - avg_cost) * h.get('quantity', 0)

    elif metric == "xp_gained":
        user = await db.users.find_one({"id": user_id})
        score = float(user.get('experience_points', 0))

    elif metric == "crises_resolved":
        count = await db.game_crises.count_documents({
            "user_id": user_id,
            "status": "resolved",
            "resolved_at": {"$gte": week_start},
        })
        score = float(count)

    elif metric == "net_worth_growth":
        user = await db.users.find_one({"id": user_id})
        score = user.get('money', 0)  # Simplified proxy

    return round(score, 2)


# ==================== ENDPOINTS ====================

@router.get("/competitions/active")
async def get_active_competitions(current_user: dict = Depends(get_current_user)):
    """Get current week's active competitions."""
    uid = current_user['id']

    # Ensure competitions exist for this week
    await ensure_weekly_competition()

    week_start, week_end = get_week_bounds()
    comps = await db.competitions.find({
        "week_start": {"$gte": week_start},
        "status": "active",
    }).to_list(10)

    result = []
    for comp in comps:
        comp.pop('_id', None)

        # Auto-join the user if not already participating
        if uid not in comp.get('participants', []):
            await db.competitions.update_one(
                {"id": comp['id']},
                {"$addToSet": {"participants": uid}}
            )

        # Get top 5 leaderboard
        participants = comp.get('participants', [])
        if uid not in participants:
            participants.append(uid)

        leaderboard = []
        for pid in participants:
            user = await db.users.find_one({"id": pid})
            if not user:
                continue
            score = await get_participant_score(pid, comp['metric'], week_start)
            leaderboard.append({
                "user_id": pid,
                "name": user.get('name', 'Jogador'),
                "avatar_color": user.get('avatar_color', 'green'),
                "level": user.get('level', 1),
                "score": score,
                "is_you": pid == uid,
            })

        leaderboard.sort(key=lambda x: x['score'], reverse=True)
        for i, entry in enumerate(leaderboard):
            entry['position'] = i + 1

        my_entry = next((e for e in leaderboard if e['is_you']), None)

        # Time remaining
        remaining = (week_end - datetime.utcnow()).total_seconds()
        days_remaining = max(0, remaining / 86400)

        comp['leaderboard'] = leaderboard[:5]
        comp['my_position'] = my_entry['position'] if my_entry else 0
        comp['my_score'] = my_entry['score'] if my_entry else 0
        comp['participant_count'] = len(participants)
        comp['days_remaining'] = round(days_remaining, 1)
        result.append(comp)

    return {"competitions": result, "count": len(result)}


@router.get("/competitions/leaderboard/{competition_id}")
async def get_competition_leaderboard(
    competition_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get full leaderboard for a specific competition."""
    uid = current_user['id']

    comp = await db.competitions.find_one({"id": competition_id})
    if not comp:
        raise HTTPException(status_code=404, detail="Competição não encontrada")

    week_start = comp.get('week_start', datetime.utcnow())
    participants = comp.get('participants', [])

    leaderboard = []
    for pid in participants:
        user = await db.users.find_one({"id": pid})
        if not user:
            continue
        score = await get_participant_score(pid, comp['metric'], week_start)
        leaderboard.append({
            "user_id": pid,
            "name": user.get('name', 'Jogador'),
            "avatar_color": user.get('avatar_color', 'green'),
            "avatar_icon": user.get('avatar_icon', 'person'),
            "level": user.get('level', 1),
            "score": score,
            "is_you": pid == uid,
        })

    leaderboard.sort(key=lambda x: x['score'], reverse=True)
    for i, entry in enumerate(leaderboard):
        entry['position'] = i + 1

    comp.pop('_id', None)
    return {"competition": comp, "leaderboard": leaderboard}


@router.post("/competitions/claim")
async def claim_competition_rewards(data: dict, current_user: dict = Depends(get_current_user)):
    """Claim rewards from a finished competition."""
    uid = current_user['id']
    comp_id = data.get('competition_id')

    if not comp_id:
        raise HTTPException(status_code=400, detail="competition_id é obrigatório")

    comp = await db.competitions.find_one({"id": comp_id})
    if not comp:
        raise HTTPException(status_code=404, detail="Competição não encontrada")

    # Check if competition has ended
    week_end = comp.get('week_end', datetime.utcnow())
    if datetime.utcnow() < week_end:
        raise HTTPException(status_code=400, detail="Competição ainda está ativa")

    # Check if already claimed
    claims = comp.get('claims', [])
    if uid in claims:
        raise HTTPException(status_code=400, detail="Recompensa já reivindicada")

    # Calculate final position
    week_start = comp.get('week_start', datetime.utcnow())
    participants = comp.get('participants', [])

    scores = []
    for pid in participants:
        user = await db.users.find_one({"id": pid})
        if not user:
            continue
        score = await get_participant_score(pid, comp['metric'], week_start)
        scores.append({"user_id": pid, "score": score})

    scores.sort(key=lambda x: x['score'], reverse=True)
    my_position = next((i + 1 for i, s in enumerate(scores) if s['user_id'] == uid), 0)

    # Find reward
    reward = None
    for r in comp.get('rewards', []):
        if r['position'] == my_position:
            reward = r
            break

    if not reward:
        return {
            "success": True,
            "position": my_position,
            "reward": None,
            "message": f"Você ficou em {my_position}o lugar. Melhor sorte na próxima!",
        }

    # Apply reward
    user = await db.users.find_one({"id": uid})
    new_exp = user.get('experience_points', 0) + reward.get('xp', 0)
    new_level = calculate_level(new_exp)

    await db.users.update_one(
        {"id": uid},
        {
            "$inc": {"money": reward.get('money', 0)},
            "$set": {"experience_points": new_exp, "level": new_level},
        }
    )

    # Mark claimed
    await db.competitions.update_one(
        {"id": comp_id},
        {
            "$push": {"claims": uid},
            "$set": {"status": "finished"},
        }
    )

    # Notification
    await db.notifications.insert_one({
        "id": str(uuid.uuid4())[:8],
        "user_id": uid,
        "type": "competition_reward",
        "title": f"🏆 {comp.get('title', 'Competição')}: {reward['label']}!",
        "message": f"Você ganhou $ {reward.get('money', 0)} + {reward.get('xp', 0)} XP!",
        "read": False,
        "created_at": datetime.utcnow(),
    })

    return {
        "success": True,
        "position": my_position,
        "reward": reward,
        "message": f"Parabéns! {reward['label']} - $ {reward.get('money', 0)} + {reward.get('xp', 0)} XP!",
    }


@router.get("/competitions/history")
async def get_competition_history(current_user: dict = Depends(get_current_user)):
    """Get past competitions."""
    week_start, _ = get_week_bounds()

    comps = await db.competitions.find({
        "week_start": {"$lt": week_start},
    }).sort("week_start", -1).to_list(20)

    for comp in comps:
        comp.pop('_id', None)

    return {"competitions": comps, "count": len(comps)}
