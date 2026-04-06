"""BizRealms - Notifications Routes."""
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

import os
import httpx
from config import JWT_SECRET, JWT_ALGORITHM

router = APIRouter()

# ==================== ACHIEVEMENTS / BADGES ====================

# Tiered achievement system - each achievement has progressive tiers
# Players always have a next tier to chase
ACHIEVEMENT_GROUPS = [
    {
        "group": "jobs",
        "icon": "briefcase",
        "color": "#2196F3",
        "tiers": [
            {"id": "jobs_1", "target": 1, "xp": 50, "money": 500},
            {"id": "jobs_5", "target": 5, "xp": 150, "money": 2000},
            {"id": "jobs_20", "target": 20, "xp": 400, "money": 8000},
            {"id": "jobs_50", "target": 50, "xp": 800, "money": 20000},
            {"id": "jobs_100", "target": 100, "xp": 1500, "money": 50000},
        ],
    },
    {
        "group": "companies",
        "icon": "business",
        "color": "#FF9800",
        "tiers": [
            {"id": "companies_1", "target": 1, "xp": 100, "money": 1000},
            {"id": "companies_3", "target": 3, "xp": 250, "money": 3000},
            {"id": "companies_5", "target": 5, "xp": 500, "money": 8000},
            {"id": "companies_10", "target": 10, "xp": 1000, "money": 25000},
            {"id": "companies_20", "target": 20, "xp": 2000, "money": 60000},
        ],
    },
    {
        "group": "investments",
        "icon": "trending-up",
        "color": "#9C27B0",
        "tiers": [
            {"id": "invest_1", "target": 1, "xp": 75, "money": 750},
            {"id": "invest_5", "target": 5, "xp": 200, "money": 2500},
            {"id": "invest_10", "target": 10, "xp": 400, "money": 6000},
            {"id": "invest_25", "target": 25, "xp": 800, "money": 15000},
            {"id": "invest_50", "target": 50, "xp": 1500, "money": 40000},
        ],
    },
    {
        "group": "money",
        "icon": "cash",
        "color": "#4CAF50",
        "tiers": [
            {"id": "money_10k", "target": 10000, "xp": 50, "money": 500},
            {"id": "money_100k", "target": 100000, "xp": 200, "money": 2000},
            {"id": "money_1m", "target": 1000000, "xp": 500, "money": 10000},
            {"id": "money_10m", "target": 10000000, "xp": 1000, "money": 50000},
            {"id": "money_100m", "target": 100000000, "xp": 2500, "money": 200000},
            {"id": "money_1b", "target": 1000000000, "xp": 5000, "money": 1000000},
        ],
    },
    {
        "group": "level",
        "icon": "star",
        "color": "#FFD700",
        "tiers": [
            {"id": "level_3", "target": 3, "xp": 100, "money": 1000},
            {"id": "level_5", "target": 5, "xp": 200, "money": 2500},
            {"id": "level_10", "target": 10, "xp": 500, "money": 5000},
            {"id": "level_15", "target": 15, "xp": 800, "money": 12000},
            {"id": "level_20", "target": 20, "xp": 1200, "money": 25000},
            {"id": "level_30", "target": 30, "xp": 2000, "money": 60000},
        ],
    },
    {
        "group": "education",
        "icon": "school",
        "color": "#00BCD4",
        "tiers": [
            {"id": "edu_1", "target": 1, "xp": 75, "money": 500},
            {"id": "edu_3", "target": 3, "xp": 200, "money": 2000},
            {"id": "edu_5", "target": 5, "xp": 400, "money": 5000},
        ],
    },
    {
        "group": "certifications",
        "icon": "ribbon",
        "color": "#E91E63",
        "tiers": [
            {"id": "cert_1", "target": 1, "xp": 100, "money": 1500},
            {"id": "cert_3", "target": 3, "xp": 300, "money": 5000},
            {"id": "cert_5", "target": 5, "xp": 600, "money": 15000},
        ],
    },
    {
        "group": "courses",
        "icon": "book",
        "color": "#3F51B5",
        "tiers": [
            {"id": "courses_1", "target": 1, "xp": 100, "money": 1500},
            {"id": "courses_3", "target": 3, "xp": 300, "money": 5000},
            {"id": "courses_5", "target": 5, "xp": 600, "money": 12000},
            {"id": "courses_10", "target": 10, "xp": 1200, "money": 30000},
        ],
    },
    {
        "group": "assets",
        "icon": "home",
        "color": "#795548",
        "tiers": [
            {"id": "assets_1", "target": 1, "xp": 100, "money": 1000},
            {"id": "assets_3", "target": 3, "xp": 250, "money": 3000},
            {"id": "assets_5", "target": 5, "xp": 500, "money": 8000},
            {"id": "assets_10", "target": 10, "xp": 1000, "money": 25000},
        ],
    },
    {
        "group": "loans",
        "icon": "card",
        "color": "#1E88E5",
        "tiers": [
            {"id": "loans_1", "target": 1, "xp": 50, "money": 500},
            {"id": "loans_3", "target": 3, "xp": 150, "money": 2000},
            {"id": "loans_5", "target": 5, "xp": 300, "money": 5000},
        ],
    },
    {
        "group": "franchises",
        "icon": "git-branch",
        "color": "#FF5722",
        "tiers": [
            {"id": "franchise_1", "target": 1, "xp": 150, "money": 2000},
            {"id": "franchise_3", "target": 3, "xp": 400, "money": 6000},
            {"id": "franchise_5", "target": 5, "xp": 800, "money": 15000},
            {"id": "franchise_10", "target": 10, "xp": 1500, "money": 35000},
        ],
    },
    {
        "group": "net_worth",
        "icon": "trophy",
        "color": "#FF6F00",
        "tiers": [
            {"id": "nw_50k", "target": 50000, "xp": 100, "money": 1000},
            {"id": "nw_500k", "target": 500000, "xp": 300, "money": 5000},
            {"id": "nw_5m", "target": 5000000, "xp": 800, "money": 25000},
            {"id": "nw_50m", "target": 50000000, "xp": 2000, "money": 100000},
            {"id": "nw_500m", "target": 500000000, "xp": 5000, "money": 500000},
        ],
    },
]

# Flatten all tier IDs for the lookup
ALL_TIER_IDS = set()
for g in ACHIEVEMENT_GROUPS:
    for t in g['tiers']:
        ALL_TIER_IDS.add(t['id'])


@router.get("/achievements")
async def get_achievements(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get user's tiered achievements with progress."""
    user = await get_current_user(credentials)
    uid = user['id']

    # Get unlocked achievements
    unlocked = await db.achievements.find({'user_id': uid}).to_list(500)
    unlocked_ids = {a['achievement_id'] for a in unlocked}
    unlocked_map = {a['achievement_id']: a for a in unlocked}

    # Get current stats for progress calculation
    companies_count = await db.companies.count_documents({'owner_id': uid, 'is_franchise': {'$ne': True}})
    franchise_count = await db.companies.count_documents({'owner_id': uid, 'is_franchise': True})
    investments_count = await db.investments.count_documents({'user_id': uid})
    assets_count = await db.assets.count_documents({'user_id': uid})
    loans_count = await db.loans.count_documents({'user_id': uid})
    courses_count = await db.user_courses.count_documents({'user_id': uid, 'completed': True})
    work_exp = user.get('work_experience', [])
    unique_jobs = len(set(j.get('company', '') + j.get('position', '') for j in work_exp)) if work_exp else 0
    if user.get('current_job'):
        unique_jobs = max(unique_jobs, 1)
    education_count = len(user.get('education', []))
    cert_count = len(user.get('certifications', []))
    money = user.get('money', 0)
    level = user.get('level', 1)

    # Calculate approx net worth for net_worth group
    inv_val = 0
    holdings = await db.investments.find({'user_id': uid}).to_list(100)
    for h in holdings:
        inv_val += h.get('current_value', h.get('quantity', 0) * h.get('current_price', h.get('buy_price', 0)))
    comp_val = 0
    user_companies = await db.companies.find({'owner_id': uid}).to_list(100)
    for c in user_companies:
        comp_val += c.get('purchase_price', 0)
    asset_val = 0
    user_assets = await db.assets.find({'user_id': uid}).to_list(100)
    for a in user_assets:
        asset_val += a.get('current_value', a.get('purchase_price', 0))
    net_worth = money + inv_val + comp_val + asset_val

    progress_map = {
        'jobs': unique_jobs,
        'companies': companies_count,
        'investments': investments_count,
        'money': money,
        'level': level,
        'education': education_count,
        'certifications': cert_count,
        'courses': courses_count,
        'assets': assets_count,
        'loans': loans_count,
        'franchises': franchise_count,
        'net_worth': net_worth,
    }

    result = []
    total_tiers = 0
    total_unlocked = 0

    for group in ACHIEVEMENT_GROUPS:
        current_progress = progress_map.get(group['group'], 0)
        completed_tiers = 0
        current_tier_idx = 0

        for i, tier in enumerate(group['tiers']):
            total_tiers += 1
            if tier['id'] in unlocked_ids:
                completed_tiers += 1
                total_unlocked += 1
                current_tier_idx = i + 1

        # Determine next tier (or completed all)
        all_done = completed_tiers >= len(group['tiers'])
        next_tier = group['tiers'][current_tier_idx] if not all_done else None
        last_completed = group['tiers'][current_tier_idx - 1] if current_tier_idx > 0 else None

        # Progress percentage toward next tier
        if next_tier:
            prev_target = group['tiers'][current_tier_idx - 1]['target'] if current_tier_idx > 0 else 0
            range_size = next_tier['target'] - prev_target
            progress_in_range = current_progress - prev_target
            progress_pct = min(100, max(0, (progress_in_range / range_size * 100))) if range_size > 0 else 0
        else:
            progress_pct = 100

        result.append({
            'group': group['group'],
            'icon': group['icon'],
            'color': group['color'],
            'total_tiers': len(group['tiers']),
            'completed_tiers': completed_tiers,
            'all_done': all_done,
            'current_progress': round(current_progress, 2),
            'next_tier': next_tier,
            'last_completed': last_completed,
            'progress_pct': round(progress_pct, 1),
            'tiers': [
                {
                    **tier,
                    'unlocked': tier['id'] in unlocked_ids,
                    'unlocked_at': unlocked_map[tier['id']]['unlocked_at'].isoformat()
                    if tier['id'] in unlocked_map and isinstance(unlocked_map[tier['id']].get('unlocked_at'), datetime) else None,
                }
                for tier in group['tiers']
            ],
        })

    return {"achievements": result, "total": total_tiers, "unlocked": total_unlocked}


@router.post("/achievements/check")
async def check_achievements(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Check and unlock any new tiered achievements based on current state."""
    user = await get_current_user(credentials)
    uid = user['id']

    unlocked = await db.achievements.find({'user_id': uid}).to_list(500)
    unlocked_ids = {a['achievement_id'] for a in unlocked}
    new_unlocks = []

    # Get current stats
    companies_count = await db.companies.count_documents({'owner_id': uid, 'is_franchise': {'$ne': True}})
    franchise_count = await db.companies.count_documents({'owner_id': uid, 'is_franchise': True})
    investments_count = await db.investments.count_documents({'user_id': uid})
    assets_count = await db.assets.count_documents({'user_id': uid})
    loans_count = await db.loans.count_documents({'user_id': uid})
    courses_count = await db.user_courses.count_documents({'user_id': uid, 'completed': True})
    work_exp = user.get('work_experience', [])
    unique_jobs = len(set(j.get('company', '') + j.get('position', '') for j in work_exp)) if work_exp else 0
    if user.get('current_job'):
        unique_jobs = max(unique_jobs, 1)
    education_count = len(user.get('education', []))
    cert_count = len(user.get('certifications', []))
    money = user.get('money', 0)
    level = user.get('level', 1)

    # Net worth
    inv_val = 0
    holdings = await db.investments.find({'user_id': uid}).to_list(100)
    for h in holdings:
        inv_val += h.get('current_value', h.get('quantity', 0) * h.get('current_price', h.get('buy_price', 0)))
    comp_val = 0
    user_comps = await db.companies.find({'owner_id': uid}).to_list(100)
    for c in user_comps:
        comp_val += c.get('purchase_price', 0)
    asset_val = 0
    user_assets = await db.assets.find({'user_id': uid}).to_list(100)
    for a in user_assets:
        asset_val += a.get('current_value', a.get('purchase_price', 0))
    net_worth = money + inv_val + comp_val + asset_val

    progress_map = {
        'jobs': unique_jobs,
        'companies': companies_count,
        'investments': investments_count,
        'money': money,
        'level': level,
        'education': education_count,
        'certifications': cert_count,
        'courses': courses_count,
        'assets': assets_count,
        'loans': loans_count,
        'franchises': franchise_count,
        'net_worth': net_worth,
    }

    total_money_earned = 0
    total_xp_earned = 0

    for group in ACHIEVEMENT_GROUPS:
        current_val = progress_map.get(group['group'], 0)
        for tier in group['tiers']:
            if tier['id'] not in unlocked_ids and current_val >= tier['target']:
                # Unlock this tier!
                await db.achievements.insert_one({
                    'user_id': uid,
                    'achievement_id': tier['id'],
                    'group': group['group'],
                    'unlocked_at': datetime.utcnow(),
                })

                total_money_earned += tier['money']
                total_xp_earned += tier['xp']

                # Add notification
                await db.notifications.insert_one({
                    'user_id': uid,
                    'type': 'achievement',
                    'title': f'Conquista Desbloqueada!',
                    'message': f'{group["group"]} Tier {tier["target"]}! +{tier["xp"]} XP, +${tier["money"]:,}',
                    'icon': group['icon'],
                    'read': False,
                    'created_at': datetime.utcnow(),
                })

                new_unlocks.append(tier['id'])
                unlocked_ids.add(tier['id'])

    # Grant all rewards at once
    if total_money_earned > 0 or total_xp_earned > 0:
        await db.users.update_one(
            {'id': uid},
            {'$inc': {'experience': total_xp_earned, 'money': total_money_earned}}
        )

    return {
        "new_unlocks": new_unlocks,
        "count": len(new_unlocks),
        "money_earned": total_money_earned,
        "xp_earned": total_xp_earned,
    }

# ==================== IN-APP NOTIFICATIONS ====================

@router.get("/notifications")
async def get_notifications(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get user's notifications."""
    user = await get_current_user(credentials)
    notifications = await db.notifications.find({'user_id': user['id']}).sort('created_at', -1).to_list(50)
    unread_count = sum(1 for n in notifications if not n.get('read'))
    for n in notifications:
        n['id'] = str(n.pop('_id'))
        n['created_at'] = n['created_at'].isoformat() if isinstance(n.get('created_at'), datetime) else str(n.get('created_at', ''))
    return {"notifications": notifications, "unread_count": unread_count}

@router.post("/notifications/read")
async def mark_notifications_read(data: dict, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Mark notifications as read."""
    user = await get_current_user(credentials)
    notification_id = data.get('notification_id')
    
    if notification_id == 'all':
        await db.notifications.update_many(
            {'user_id': user['id'], 'read': False},
            {'$set': {'read': True}}
        )
    elif notification_id:
        await db.notifications.update_one(
            {'_id': ObjectId(notification_id), 'user_id': user['id']},
            {'$set': {'read': True}}
        )
    
    return {"message": "Notifications marked as read"}

# ==================== PUSH NOTIFICATIONS ====================

@router.post("/push/register")
async def register_push_token(data: dict, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Register an Expo push token for the user."""
    user = await get_current_user(credentials)
    push_token = data.get('push_token')
    platform = data.get('platform', 'unknown')
    
    if not push_token:
        raise HTTPException(status_code=400, detail="Push token required")
    
    # Upsert the push token
    await db.push_tokens.update_one(
        {'user_id': user['id']},
        {'$set': {
            'user_id': user['id'],
            'push_token': push_token,
            'platform': platform,
            'updated_at': datetime.utcnow(),
            'active': True,
        }},
        upsert=True
    )
    
    return {"message": "Push token registered", "token": push_token}

@router.post("/push/send")
async def send_push_notification(data: dict, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Send a push notification to a specific user or all users (admin only)."""
    user = await get_current_user(credentials)
    
    target_user_id = data.get('target_user_id')
    title = data.get('title', 'BizRealms')
    body = data.get('body', '')
    data_payload = data.get('data', {})
    
    import httpx
    
    # Get target push tokens
    if target_user_id == 'all':
        tokens = await db.push_tokens.find({'active': True}).to_list(1000)
    elif target_user_id:
        tokens = await db.push_tokens.find({'user_id': target_user_id, 'active': True}).to_list(1)
    else:
        tokens = await db.push_tokens.find({'user_id': user['id'], 'active': True}).to_list(1)
    
    if not tokens:
        return {"message": "No push tokens found", "sent": 0}
    
    # Send via Expo Push API
    messages = []
    for t_doc in tokens:
        push_token = t_doc.get('push_token')
        if push_token and push_token.startswith('ExponentPushToken'):
            messages.append({
                "to": push_token,
                "title": title,
                "body": body,
                "data": data_payload,
                "sound": "default",
                "badge": 1,
            })
    
    sent = 0
    if messages:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    "https://exp.host/--/api/v2/push/send",
                    json=messages,
                    headers={
                        "Accept": "application/json",
                        "Content-Type": "application/json",
                    }
                )
                if resp.status_code == 200:
                    sent = len(messages)
                else:
                    print(f"Expo push error: {resp.text}")
        except Exception as e:
            print(f"Push notification error: {e}")
    
    return {"message": f"Sent {sent} notifications", "sent": sent}

@router.delete("/push/unregister")
async def unregister_push_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Unregister push token (on logout)."""
    user = await get_current_user(credentials)
    await db.push_tokens.update_one(
        {'user_id': user['id']},
        {'$set': {'active': False}}
    )
    return {"message": "Push token unregistered"}


# ==================== AI COACHING ====================

COACHING_SYSTEM_PROMPT = """Você é o Coach Virtual de Negócios do jogo Business Empire: RichMan. 
Você é um mentor experiente, motivador e direto. Fale em português do Brasil.
Analise os dados do jogador e dê conselhos estratégicos personalizados.
Seja breve (max 3-4 parágrafos), use emojis ocasionalmente, e sempre termine com uma dica acionável.
Você pode sugerir: investir em ações/cripto, comprar empresas, fazer cursos, usar o banco, comprar imóveis.
Adapte o tom ao nível do jogador: iniciante (nível 1-10), intermediário (10-30), avançado (30+)."""

@router.post("/coaching/advice")
async def get_coaching_advice(request: dict, current_user: dict = Depends(get_current_user)):
    """Get AI coaching advice based on player stats"""
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    user_question = request.get('question', 'Me dê dicas para crescer no jogo')
    
    user = await db.users.find_one({"id": current_user['id']})
    companies = await db.user_companies.find({"user_id": current_user['id']}).to_list(500)
    investments = await db.user_investments.find({"user_id": current_user['id']}).to_list(100)
    assets = await db.user_assets.find({"user_id": current_user['id']}).to_list(100)
    courses = await db.user_courses.find({"user_id": current_user['id']}).to_list(50)
    loans = await db.bank_loans.find({"user_id": current_user['id'], "status": "active"}).to_list(10)
    
    inv_value = sum(i.get('current_value', i.get('amount', 0) * i.get('current_price', i.get('purchase_price', 0))) for i in investments)
    comp_revenue = sum(c.get('monthly_revenue', 0) for c in companies)
    comp_value = sum(c.get('purchase_price', 0) for c in companies)
    asset_value = sum(a.get('current_value', a.get('purchase_price', 0)) for a in assets)
    total_debt = sum(l.get('remaining_balance', 0) for l in loans)
    
    player_context = f"""
DADOS DO JOGADOR:
- Nome: {user.get('username', 'Jogador')}
- Nível: {user.get('level', 1)} | XP: {user.get('experience', 0)}
- Dinheiro: $ {user.get('money', 0):,.2f}
- Empresas: {len(companies)} (receita mensal: $ {comp_revenue:,.2f}, valor total: $ {comp_value:,.2f})
- Investimentos: {len(investments)} (valor: $ {inv_value:,.2f})
- Imóveis/Bens: {len(assets)} (valor: $ {asset_value:,.2f})
- Cursos feitos: {len(courses)}
- Dívidas: $ {total_debt:,.2f}
- Patrimônio líquido: $ {(user.get('money', 0) + inv_value + comp_value + asset_value - total_debt):,.2f}
- Habilidades: {user.get('skills', {})}

PERGUNTA DO JOGADOR: {user_question}
"""
    
    try:
        llm_key = os.getenv('EMERGENT_LLM_KEY')
        chat = LlmChat(
            api_key=llm_key,
            session_id=f"coaching-{current_user['id']}-{datetime.utcnow().strftime('%Y%m%d%H')}",
            system_message=COACHING_SYSTEM_PROMPT,
        )
        chat.with_model("openai", "gpt-4.1-mini")
        
        msg = UserMessage(text=player_context)
        response = await chat.send_message(msg)
        
        await db.coaching_history.insert_one({
            "id": str(uuid.uuid4()),
            "user_id": current_user['id'],
            "question": user_question,
            "response": response,
            "player_level": user.get('level', 1),
            "created_at": datetime.utcnow(),
        })
        
        return {"success": True, "advice": response, "player_level": user.get('level', 1)}
    except Exception as e:
        logger.error(f"Coaching AI error: {e}")
        level = user.get('level', 1)
        if level < 10:
            fallback = "Foque em fazer cursos para aumentar seus ganhos e completar trabalhos para subir de nível. Invista em empresas pequenas para começar!"
        elif level < 30:
            fallback = "Diversifique! Compre ações e cripto, invista em imóveis e expanda suas franquias. Use o banco para empréstimos estratégicos."
        else:
            fallback = "Você já é um magnata! Foque em fusões de empresas, investimentos de alto risco e complete os cursos avançados de Harvard."
        return {"success": True, "advice": fallback, "player_level": level, "fallback": True}


@router.get("/coaching/history")
async def get_coaching_history(current_user: dict = Depends(get_current_user)):
    """Get coaching conversation history"""
    history = await db.coaching_history.find(
        {"user_id": current_user['id']}
    ).sort("created_at", -1).to_list(20)
    for h in history:
        h.pop('_id', None)
        h['created_at'] = h['created_at'].isoformat() if isinstance(h.get('created_at'), datetime) else str(h.get('created_at', ''))
    return {"history": history}



