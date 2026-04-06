"""BizRealms - Rankings Routes."""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional
from datetime import datetime, timedelta
from bson import ObjectId
import uuid
import random
import math

from database import db
from utils import get_current_user, hash_password, verify_password, create_token, decode_token, calculate_level, security
from models import (
    Education, Certification, WorkExperience, User, UserCreate, UserLogin,
    TokenResponse, UserResponse, EducationCreate, CertificationCreate,
    CharacterProfileUpdate, BackgroundOption, DreamOption, Job, JobApplication,
    Course, UserCourse, JobApplyRequest, CourseEnrollRequest, WorkRequest,
    AdBoost, UserCourseComplete, SocialAuthRequest,
)

# Import the get_current_price function from investments module
from routes.investments import get_current_price


router = APIRouter()

# ==================== RANKINGS (CLASSIFICAÇÃO) ====================

async def calculate_user_net_worth(user: dict) -> dict:
    """Calculate total net worth for a user"""
    user_id = user['id']
    cash = user.get('money', 0)

    # Investment holdings value
    investment_value = 0
    holdings = await db.user_holdings.find({"user_id": user_id}).to_list(200)
    for h in holdings:
        asset = await db.investment_assets.find_one({"id": h['asset_id']})
        if asset:
            current_price = get_current_price(asset)
            investment_value += h['quantity'] * current_price

    # Companies value (purchase_price + accumulated value)
    companies_value = 0
    companies_revenue = 0
    companies = await db.user_companies.find({"user_id": user_id}).to_list(200)
    for c in companies:
        companies_value += c.get('purchase_price', 0)
        companies_revenue += c.get('monthly_revenue', 0)

    # Assets value (with appreciation/depreciation)
    assets_value = 0
    assets = await db.user_assets.find({"user_id": user_id}).to_list(200)
    for a in assets:
        purchase_price = a.get('purchase_price', 0)
        rate = a.get('appreciation_rate', 0) / 100
        purchased_at = a.get('purchased_at', datetime.utcnow())
        if isinstance(purchased_at, str):
            purchased_at = datetime.fromisoformat(purchased_at.replace('Z', '+00:00'))
        days = (datetime.utcnow() - purchased_at).days
        current_val = purchase_price * (1 + rate * days / 365)
        assets_value += max(0, current_val)

    total = cash + investment_value + companies_value + assets_value

    # Certification bonus: +5% per certification, max +25% (5 certs)
    certifications = user.get('certifications', [])
    cert_count = len(certifications)
    cert_bonus_pct = min(cert_count * 5, 25)  # 5% per cert, max 25%
    cert_bonus_value = total * (cert_bonus_pct / 100)
    total_with_bonus = total + cert_bonus_value

    return {
        "user_id": user_id,
        "name": user.get('name', 'Jogador'),
        "avatar_color": user.get('avatar_color', 'green'),
        "avatar_icon": user.get('avatar_icon', 'person'),
        "avatar_photo": user.get('avatar_photo'),
        "level": user.get('level', 1),
        "cash": round(cash, 2),
        "investment_value": round(investment_value, 2),
        "companies_value": round(companies_value, 2),
        "companies_revenue": round(companies_revenue, 2),
        "assets_value": round(assets_value, 2),
        "total_net_worth": round(total_with_bonus, 2),
        "base_net_worth": round(total, 2),
        "cert_bonus_pct": cert_bonus_pct,
        "cert_bonus_value": round(cert_bonus_value, 2),
        "cert_count": cert_count,
        "num_companies": len(companies),
        "num_assets": len(assets),
        "num_investments": len(holdings),
    }


@router.get("/rankings")
async def get_rankings(
    period: str = "weekly",
    current_user: dict = Depends(get_current_user)
):
    """Get player rankings by net worth"""
    # Fetch all users
    all_users = await db.users.find({}).to_list(500)

    # Calculate net worth for each user
    rankings = []
    for u in all_users:
        nw = await calculate_user_net_worth(u)
        rankings.append(nw)

    # Sort by total net worth descending
    rankings.sort(key=lambda x: x['total_net_worth'], reverse=True)

    # Assign positions
    for i, r in enumerate(rankings):
        r['position'] = i + 1

    # Find current user position
    current_position = next((r for r in rankings if r['user_id'] == current_user['id']), None)

    # Get previous ranking snapshot for comparison
    snapshot_key = f"ranking_{period}"
    now = datetime.utcnow()

    if period == "weekly":
        cutoff = now - timedelta(days=7)
    else:
        cutoff = now - timedelta(days=30)

    # Fetch previous snapshot
    prev_snapshot = await db.ranking_snapshots.find_one(
        {"type": period, "created_at": {"$gte": cutoff}},
        sort=[("created_at", -1)]
    )

    # Calculate position changes
    prev_positions = {}
    if prev_snapshot and 'rankings' in prev_snapshot:
        for pr in prev_snapshot['rankings']:
            prev_positions[pr['user_id']] = pr['position']

    for r in rankings:
        prev_pos = prev_positions.get(r['user_id'])
        if prev_pos is not None:
            r['position_change'] = prev_pos - r['position']  # positive = moved up
        else:
            r['position_change'] = 0
            r['is_new'] = True

    # Save current snapshot (max 1 per hour to avoid spam)
    last_save = await db.ranking_snapshots.find_one(
        {"type": period},
        sort=[("created_at", -1)]
    )
    should_save = True
    if last_save:
        last_time = last_save.get('created_at', datetime.min)
        if isinstance(last_time, str):
            last_time = datetime.fromisoformat(last_time.replace('Z', '+00:00'))
        if (now - last_time).total_seconds() < 3600:
            should_save = False

    if should_save:
        snapshot = {
            "type": period,
            "created_at": now,
            "rankings": [{"user_id": r['user_id'], "position": r['position'], "total_net_worth": r['total_net_worth']} for r in rankings[:50]]
        }
        await db.ranking_snapshots.insert_one(snapshot)

    # Top 50
    top_rankings = rankings[:50]

    # Check if current user has unclaimed rewards
    unclaimed = await db.ranking_rewards.find_one({
        "user_id": current_user['id'],
        "claimed": False
    })

    return {
        "period": period,
        "updated_at": now.isoformat(),
        "total_players": len(rankings),
        "rankings": top_rankings,
        "current_user": current_position,
        "has_unclaimed_reward": unclaimed is not None,
        "unclaimed_reward": {
            "position": unclaimed['position'],
            "reward_type": unclaimed['reward_type'],
            "reward_description": unclaimed['reward_description'],
            "week_of": unclaimed.get('week_of', ''),
        } if unclaimed else None,
        "prizes": [
            {"position": 1, "icon": "star", "color": "#FFD700", "description": "+50.000 XP", "type": "xp"},
            {"position": 2, "icon": "flash", "color": "#C0C0C0", "description": "Boost 5x por 24h", "type": "boost"},
            {"position": 3, "icon": "cash", "color": "#CD7F32", "description": "+$ 25.000", "type": "money"},
        ],
    }


WEEKLY_PRIZES = {
    1: {"type": "xp", "value": 50000, "description": "+50.000 XP de experiência"},
    2: {"type": "boost", "multiplier": 5.0, "duration_hours": 24, "description": "Boost 5x nos ganhos por 24 horas"},
    3: {"type": "money", "value": 25000, "description": "+$ 25.000 em dinheiro do jogo"},
}


@router.post("/rankings/distribute-rewards")
async def distribute_weekly_rewards(current_user: dict = Depends(get_current_user)):
    """Distribute weekly rewards to top 3 players. Can be called by any user, runs once per week."""
    now = datetime.utcnow()

    # Check if rewards already distributed this week
    last_distribution = await db.ranking_distributions.find_one(
        {},
        sort=[("created_at", -1)]
    )
    if last_distribution:
        last_time = last_distribution.get('created_at', datetime.min)
        if isinstance(last_time, str):
            last_time = datetime.fromisoformat(last_time.replace('Z', '+00:00'))
        if (now - last_time).total_seconds() < 604800:  # 7 days
            days_left = 7 - int((now - last_time).total_seconds() / 86400)
            return {
                "distributed": False,
                "message": f"Prêmios já distribuídos esta semana. Próxima distribuição em {days_left} dia(s).",
                "next_distribution_in_days": days_left,
            }

    # Calculate current rankings
    all_users = await db.users.find({}).to_list(500)
    rankings = []
    for u in all_users:
        nw = await calculate_user_net_worth(u)
        rankings.append(nw)
    rankings.sort(key=lambda x: x['total_net_worth'], reverse=True)

    # Distribute rewards to top 3
    week_label = now.strftime("%Y-W%U")
    winners = []

    for pos in range(1, 4):
        if pos > len(rankings):
            break
        winner = rankings[pos - 1]
        prize = WEEKLY_PRIZES[pos]

        # Create reward record
        reward = {
            "id": str(uuid.uuid4()),
            "user_id": winner['user_id'],
            "position": pos,
            "reward_type": prize['type'],
            "reward_description": prize['description'],
            "reward_data": prize,
            "week_of": week_label,
            "claimed": False,
            "created_at": now,
        }
        await db.ranking_rewards.insert_one(reward)

        winners.append({
            "position": pos,
            "name": winner['name'],
            "net_worth": winner['total_net_worth'],
            "prize": prize['description'],
        })

    # Record distribution
    await db.ranking_distributions.insert_one({
        "created_at": now,
        "week_of": week_label,
        "winners": winners,
    })

    return {
        "distributed": True,
        "message": "Prêmios semanais distribuídos com sucesso!",
        "week_of": week_label,
        "winners": winners,
    }


@router.post("/rankings/claim-reward")
async def claim_ranking_reward(current_user: dict = Depends(get_current_user)):
    """Claim an unclaimed ranking reward"""
    reward = await db.ranking_rewards.find_one({
        "user_id": current_user['id'],
        "claimed": False,
    })

    if not reward:
        raise HTTPException(status_code=404, detail="Nenhum prêmio disponível para resgatar")

    user = await db.users.find_one({"id": current_user['id']})
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    prize_data = reward.get('reward_data', {})
    prize_type = prize_data.get('type', '')
    messages = []
    update_ops: dict = {}

    if prize_type == 'xp':
        xp_amount = prize_data.get('value', 50000)
        new_xp = user.get('experience_points', 0) + xp_amount
        new_level = (new_xp // 1000) + 1
        update_ops['experience_points'] = new_xp
        update_ops['level'] = new_level
        messages.append(f"+{xp_amount:,} XP! Agora nível {new_level}")

    elif prize_type == 'money':
        money_amount = prize_data.get('value', 25000)
        new_money = user.get('money', 0) + money_amount
        update_ops['money'] = new_money
        messages.append(f"+$ {money_amount:,.0f} adicionados à sua conta!")

    elif prize_type == 'boost':
        multiplier = prize_data.get('multiplier', 5.0)
        duration_hours = prize_data.get('duration_hours', 24)
        now = datetime.utcnow()
        expires_at = now + timedelta(hours=duration_hours)

        existing_boost = await db.ad_boosts.find_one({"user_id": current_user['id']})
        if existing_boost:
            old_expires = existing_boost.get('expires_at', now)
            if isinstance(old_expires, str):
                old_expires = datetime.fromisoformat(old_expires.replace('Z', '+00:00'))
            new_expires = max(old_expires, expires_at)
            new_mult = max(existing_boost.get('multiplier', 1.0), multiplier)
            await db.ad_boosts.update_one(
                {"_id": existing_boost['_id']},
                {"$set": {"multiplier": new_mult, "expires_at": new_expires}}
            )
        else:
            boost = AdBoost(
                user_id=current_user['id'],
                multiplier=multiplier,
                ads_watched=0,
                expires_at=expires_at
            )
            await db.ad_boosts.insert_one(boost.dict())
        messages.append(f"Boost {multiplier}x ativado por {duration_hours}h!")

    # Apply user updates
    if update_ops:
        await db.users.update_one({"id": current_user['id']}, {"$set": update_ops})

    # Mark reward as claimed
    await db.ranking_rewards.update_one(
        {"_id": reward['_id']},
        {"$set": {"claimed": True, "claimed_at": datetime.utcnow()}}
    )

    return {
        "success": True,
        "message": " | ".join(messages),
        "position": reward['position'],
        "reward_type": prize_type,
        "reward_description": reward['reward_description'],
    }


# ==================== REAL MONEY REWARDS (PREMIAÇÃO REAL) ====================

@router.get("/rewards/prize-pool")
async def get_prize_pool(current_user: dict = Depends(get_current_user)):
    """Get current monthly prize pool and distribution info"""
    now = datetime.utcnow()
    current_month = now.strftime("%Y-%m")
    
    # Simulated ad revenue (in production, this comes from real ad network)
    # Base: $ 5000/month simulated ad revenue, 5% goes to prize pool
    total_players = await db.users.count_documents({})
    base_revenue = 5000 + (total_players * 50)  # More players = more ad revenue
    prize_pool_total = round(base_revenue * 0.05, 2)  # 5% of ad revenue
    
    # Distribution: 60% 1st, 30% 2nd, 10% 3rd
    distribution = {
        "1st": round(prize_pool_total * 0.60, 2),
        "2nd": round(prize_pool_total * 0.30, 2),
        "3rd": round(prize_pool_total * 0.10, 2),
    }
    
    # Get current monthly rankings (top 3)
    all_users = await db.users.find({}).to_list(1000)
    rankings = []
    for u in all_users:
        portfolio = await db.user_investments.find({"user_id": u['id']}).to_list(100)
        inv_value = sum(i.get('current_value', i.get('amount', 0) * i.get('current_price', i.get('purchase_price', 0))) for i in portfolio)
        companies = await db.user_companies.find({"user_id": u['id']}).to_list(500)
        comp_value = sum(c.get('purchase_price', 0) for c in companies)
        assets = await db.user_assets.find({"user_id": u['id']}).to_list(100)
        asset_value = sum(a.get('current_value', a.get('purchase_price', 0)) for a in assets)
        total_nw = u.get('money', 0) + inv_value + comp_value + asset_value
        rankings.append({
            "user_id": u['id'],
            "username": u.get('username', 'Jogador'),
            "avatar_color": u.get('avatar_color', 'blue'),
            "level": u.get('level', 1),
            "total_net_worth": round(total_nw, 2),
        })
    rankings.sort(key=lambda x: x['total_net_worth'], reverse=True)
    top3 = rankings[:3]
    
    # Check user's position
    user_pos = next((i + 1 for i, r in enumerate(rankings) if r['user_id'] == current_user['id']), None)
    
    # Check if user has PayPal configured
    user_doc = await db.users.find_one({"id": current_user['id']})
    has_paypal = bool(user_doc.get('paypal_email'))
    
    # Check if there are unclaimed real rewards for user
    unclaimed_real = await db.real_money_rewards.find_one({
        "user_id": current_user['id'],
        "claimed": False,
    })
    
    # Check previous months' rewards history
    history = await db.real_money_rewards.find({
        "user_id": current_user['id']
    }).sort("month", -1).to_list(12)
    for h in history:
        h.pop('_id', None)
    
    # Days remaining in month
    import calendar
    _, last_day = calendar.monthrange(now.year, now.month)
    days_remaining = last_day - now.day
    
    return {
        "current_month": current_month,
        "prize_pool_total": prize_pool_total,
        "distribution": distribution,
        "simulated_ad_revenue": base_revenue,
        "top3": top3,
        "user_position": user_pos,
        "total_players": total_players,
        "has_paypal": has_paypal,
        "paypal_email": user_doc.get('paypal_email', ''),
        "days_remaining": days_remaining,
        "has_unclaimed_reward": unclaimed_real is not None,
        "unclaimed_reward": {
            "amount": unclaimed_real.get('amount', 0),
            "position": unclaimed_real.get('position', 0),
            "month": unclaimed_real.get('month', ''),
            "id": unclaimed_real.get('id', ''),
        } if unclaimed_real else None,
        "history": history,
    }


@router.post("/rewards/update-paypal")
async def update_paypal_email(request: dict, current_user: dict = Depends(get_current_user)):
    """Update user's PayPal email for receiving real money rewards"""
    paypal_email = request.get('paypal_email', '').strip()

    if not paypal_email:
        raise HTTPException(status_code=400, detail="PayPal email cannot be empty")
    if '@' not in paypal_email or '.' not in paypal_email:
        raise HTTPException(status_code=400, detail="Invalid email format")

    await db.users.update_one({"id": current_user['id']}, {
        "$set": {
            "paypal_email": paypal_email,
            "paypal_updated_at": datetime.utcnow(),
        }
    })

    return {"success": True, "message": f"PayPal updated: {paypal_email}"}

@router.delete("/rewards/delete-paypal")
async def delete_paypal_email(current_user: dict = Depends(get_current_user)):
    """Remove user's PayPal email."""
    await db.users.update_one({"id": current_user['id']}, {
        "$unset": {
            "paypal_email": "",
            "paypal_updated_at": "",
        }
    })
    return {"success": True, "message": "PayPal removed successfully"}


@router.post("/rewards/distribute-monthly")
async def distribute_monthly_rewards(current_user: dict = Depends(get_current_user)):
    """Distribute monthly real money rewards to top 3 (admin/auto trigger)"""
    now = datetime.utcnow()
    current_month = now.strftime("%Y-%m")
    
    # Check if already distributed this month
    existing = await db.real_money_rewards.find_one({"month": current_month})
    if existing:
        return {"success": False, "message": "Premiação deste mês já foi distribuída"}
    
    # Calculate prize pool
    total_players = await db.users.count_documents({})
    base_revenue = 5000 + (total_players * 50)
    prize_pool_total = round(base_revenue * 0.05, 2)
    
    # Get rankings
    all_users = await db.users.find({}).to_list(1000)
    rankings = []
    for u in all_users:
        portfolio = await db.user_investments.find({"user_id": u['id']}).to_list(100)
        inv_value = sum(i.get('current_value', i.get('amount', 0) * i.get('current_price', i.get('purchase_price', 0))) for i in portfolio)
        companies = await db.user_companies.find({"user_id": u['id']}).to_list(500)
        comp_value = sum(c.get('purchase_price', 0) for c in companies)
        assets = await db.user_assets.find({"user_id": u['id']}).to_list(100)
        asset_value = sum(a.get('current_value', a.get('purchase_price', 0)) for a in assets)
        total_nw = u.get('money', 0) + inv_value + comp_value + asset_value
        rankings.append({"user_id": u['id'], "username": u.get('username', 'Jogador'), "total_net_worth": total_nw})
    rankings.sort(key=lambda x: x['total_net_worth'], reverse=True)
    
    # Distribute to top 3
    prizes = [0.60, 0.30, 0.10]
    for i, pct in enumerate(prizes):
        if i >= len(rankings):
            break
        amount = round(prize_pool_total * pct, 2)
        reward = {
            "id": str(uuid.uuid4()),
            "user_id": rankings[i]['user_id'],
            "username": rankings[i]['username'],
            "month": current_month,
            "position": i + 1,
            "amount": amount,
            "total_net_worth": rankings[i]['total_net_worth'],
            "claimed": False,
            "created_at": now,
        }
        await db.real_money_rewards.insert_one(reward)
    
    return {"success": True, "message": f"Premiação de {current_month} distribuída! Pool: $ {prize_pool_total:.2f}"}


@router.post("/rewards/claim-real")
async def claim_real_money_reward(request: dict, current_user: dict = Depends(get_current_user)):
    """Claim a real money reward (requires PayPal)"""
    reward_id = request.get('reward_id')
    
    # Check PayPal
    user = await db.users.find_one({"id": current_user['id']})
    if not user.get('paypal_email'):
        raise HTTPException(status_code=400, detail="Set up your PayPal email in your profile before claiming!")
    
    reward = await db.real_money_rewards.find_one({
        "id": reward_id,
        "user_id": current_user['id'],
        "claimed": False,
    })
    if not reward:
        raise HTTPException(status_code=404, detail="Recompensa não encontrada ou já resgatada")
    
    # Mark as claimed
    await db.real_money_rewards.update_one({"id": reward_id}, {
        "$set": {
            "claimed": True,
            "claimed_at": datetime.utcnow(),
            "paypal_email_used": user.get('paypal_email'),
            "status": "processing",  # In production: pending -> processing -> paid
        }
    })
    
    return {
        "success": True,
        "message": f"Resgate de $ {reward['amount']:.2f} solicitado!\n\nPagamento será enviado para seu PayPal: {user.get('paypal_email', '')}\n\nPrazo: até 5 dias úteis.",
        "amount": reward['amount'],
        "position": reward['position'],
    }
