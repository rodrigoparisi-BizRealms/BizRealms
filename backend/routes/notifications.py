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

ACHIEVEMENTS = [
    {"id": "first_job", "icon": "briefcase", "color": "#2196F3", "xp": 50, "money": 500},
    {"id": "first_company", "icon": "business", "color": "#FF9800", "xp": 100, "money": 1000},
    {"id": "first_investment", "icon": "trending-up", "color": "#9C27B0", "xp": 75, "money": 750},
    {"id": "millionaire", "icon": "cash", "color": "#4CAF50", "xp": 500, "money": 5000},
    {"id": "level_5", "icon": "star", "color": "#FFD700", "xp": 200, "money": 2000},
    {"id": "level_10", "icon": "trophy", "color": "#FFD700", "xp": 500, "money": 5000},
    {"id": "five_companies", "icon": "storefront", "color": "#FF5722", "xp": 300, "money": 3000},
    {"id": "ten_investments", "icon": "analytics", "color": "#00BCD4", "xp": 250, "money": 2500},
    {"id": "first_loan", "icon": "card", "color": "#1E88E5", "xp": 50, "money": 500},
    {"id": "collector", "icon": "wallet", "color": "#E91E63", "xp": 150, "money": 1500},
]

@router.get("/achievements")
async def get_achievements(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get user's achievements and available ones."""
    user = await get_current_user(credentials)
    
    # Get unlocked achievements
    unlocked = await db.achievements.find({'user_id': user['id']}).to_list(100)
    unlocked_ids = {a['achievement_id'] for a in unlocked}
    
    result = []
    for ach in ACHIEVEMENTS:
        is_unlocked = ach['id'] in unlocked_ids
        unlocked_data = next((a for a in unlocked if a.get('achievement_id') == ach['id']), None)
        result.append({
            **ach,
            'unlocked': is_unlocked,
            'unlocked_at': unlocked_data['unlocked_at'].isoformat() if unlocked_data and isinstance(unlocked_data.get('unlocked_at'), datetime) else None,
        })
    
    return {"achievements": result, "total": len(ACHIEVEMENTS), "unlocked": len(unlocked_ids)}

@router.post("/achievements/check")
async def check_achievements(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Check and unlock any new achievements based on current state."""
    user = await get_current_user(credentials)
    uid = user['id']
    
    unlocked = await db.achievements.find({'user_id': uid}).to_list(100)
    unlocked_ids = {a['achievement_id'] for a in unlocked}
    new_unlocks = []
    
    # Check conditions
    jobs = await db.users.find_one({'id': uid})
    companies = await db.companies.count_documents({'owner_id': uid})
    investments = await db.investments.count_documents({'user_id': uid})
    money = user.get('money', 0)
    level = user.get('level', 1)
    loans = await db.loans.count_documents({'user_id': uid})
    
    conditions = {
        'first_job': user.get('current_job') is not None,
        'first_company': companies >= 1,
        'first_investment': investments >= 1,
        'millionaire': money >= 1_000_000,
        'level_5': level >= 5,
        'level_10': level >= 10,
        'five_companies': companies >= 5,
        'ten_investments': investments >= 10,
        'first_loan': loans >= 1,
        'collector': money >= 100_000,
    }
    
    for ach_id, condition in conditions.items():
        if condition and ach_id not in unlocked_ids:
            ach_data = next((a for a in ACHIEVEMENTS if a['id'] == ach_id), None)
            if ach_data:
                await db.achievements.insert_one({
                    'user_id': uid,
                    'achievement_id': ach_id,
                    'unlocked_at': datetime.utcnow(),
                })
                
                # Grant rewards
                await db.users.update_one(
                    {'id': uid},
                    {'$inc': {'experience': ach_data['xp'], 'money': ach_data['money']}}
                )
                
                # Add notification
                await db.notifications.insert_one({
                    'user_id': uid,
                    'type': 'achievement',
                    'title': f'Achievement Unlocked!',
                    'message': f'You unlocked "{ach_id}"! +{ach_data["xp"]} XP, +${ach_data["money"]}',
                    'icon': ach_data['icon'],
                    'read': False,
                    'created_at': datetime.utcnow(),
                })
                
                new_unlocks.append(ach_id)
    
    return {"new_unlocks": new_unlocks, "count": len(new_unlocks)}

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
- Dinheiro: R$ {user.get('money', 0):,.2f}
- Empresas: {len(companies)} (receita mensal: R$ {comp_revenue:,.2f}, valor total: R$ {comp_value:,.2f})
- Investimentos: {len(investments)} (valor: R$ {inv_value:,.2f})
- Imóveis/Bens: {len(assets)} (valor: R$ {asset_value:,.2f})
- Cursos feitos: {len(courses)}
- Dívidas: R$ {total_debt:,.2f}
- Patrimônio líquido: R$ {(user.get('money', 0) + inv_value + comp_value + asset_value - total_debt):,.2f}
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



