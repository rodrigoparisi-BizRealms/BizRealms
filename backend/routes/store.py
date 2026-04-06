"""BizRealms - Store Routes."""
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

import stripe
import os
from config import JWT_SECRET, JWT_ALGORITHM

router = APIRouter()

STORE_ITEMS = [
    # Money Packs
    {"id": "pack_starter", "category": "dinheiro", "name": "Pacote Iniciante", "description": "Dê o primeiro passo no mundo dos negócios", "game_reward": {"money": 10000}, "price_brl": 4.90, "icon": "cash", "color": "#4CAF50", "popular": False},
    {"id": "pack_empreendedor", "category": "dinheiro", "name": "Pacote Empreendedor", "description": "Capital para abrir seu primeiro negócio", "game_reward": {"money": 50000}, "price_brl": 19.90, "icon": "cash", "color": "#4CAF50", "popular": True, "best_value": False},
    {"id": "pack_investidor", "category": "dinheiro", "name": "Pacote Investidor", "description": "Invista pesado e diversifique seus ativos", "game_reward": {"money": 200000}, "price_brl": 49.90, "icon": "wallet", "color": "#2196F3", "popular": False, "best_value": False},
    {"id": "pack_magnata", "category": "dinheiro", "name": "Pacote Magnata", "description": "Dinheiro suficiente para dominar o mercado", "game_reward": {"money": 1000000}, "price_brl": 99.90, "icon": "diamond", "color": "#FFD700", "popular": False, "best_value": True},
    {"id": "pack_bilionario", "category": "dinheiro", "name": "Pacote Bilionário", "description": "O poder de um verdadeiro bilionário nas suas mãos", "game_reward": {"money": 5000000}, "price_brl": 199.90, "icon": "trophy", "color": "#FF6B6B", "popular": False, "best_value": False},
    # XP Boosts
    {"id": "xp_small", "category": "xp", "name": "Boost XP Pequeno", "description": "Ganhe +5.000 XP instantaneamente", "game_reward": {"xp": 5000}, "price_brl": 2.90, "icon": "star", "color": "#FF9800", "popular": False},
    {"id": "xp_medium", "category": "xp", "name": "Boost XP Médio", "description": "Ganhe +25.000 XP e suba vários níveis", "game_reward": {"xp": 25000}, "price_brl": 9.90, "icon": "star", "color": "#FF9800", "popular": True},
    {"id": "xp_large", "category": "xp", "name": "Boost XP Grande", "description": "Ganhe +100.000 XP e desbloqueie itens premium", "game_reward": {"xp": 100000}, "price_brl": 29.90, "icon": "rocket", "color": "#FF9800", "popular": False, "best_value": True},
    # Earnings Boosts
    {"id": "earnings_2x_1h", "category": "ganhos", "name": "Boost 2x (1 hora)", "description": "Dobre todos os seus ganhos por 1 hora", "game_reward": {"earnings_multiplier": 2.0, "duration_hours": 1}, "price_brl": 1.90, "icon": "flash", "color": "#E91E63", "popular": False},
    {"id": "earnings_3x_3h", "category": "ganhos", "name": "Boost 3x (3 horas)", "description": "Triplique todos os seus ganhos por 3 horas", "game_reward": {"earnings_multiplier": 3.0, "duration_hours": 3}, "price_brl": 4.90, "icon": "flash", "color": "#E91E63", "popular": True},
    {"id": "earnings_5x_6h", "category": "ganhos", "name": "Boost 5x (6 horas)", "description": "Quintuplique seus ganhos por 6 horas inteiras!", "game_reward": {"earnings_multiplier": 5.0, "duration_hours": 6}, "price_brl": 9.90, "icon": "flash", "color": "#E91E63", "popular": False, "best_value": True},
    {"id": "earnings_10x_12h", "category": "ganhos", "name": "Boost 10x (12 horas)", "description": "O boost MÁXIMO! 10x ganhos por 12 horas", "game_reward": {"earnings_multiplier": 10.0, "duration_hours": 12}, "price_brl": 19.90, "icon": "rocket", "color": "#E91E63", "popular": False},
    # Ad-Free Subscription
    {"id": "ad_free_monthly", "category": "premium", "name": "Sem Propagandas", "description": "Remova todos os anúncios e ganhe bônus automáticos por 30 dias", "game_reward": {"ad_free": True, "duration_days": 30}, "price_brl": 9.90, "icon": "shield-checkmark", "color": "#9C27B0", "popular": True, "is_subscription": True},
]

@router.get("/store/items")
async def get_store_items(category: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    """Get all items available in the game store"""
    items = STORE_ITEMS
    if category:
        items = [i for i in items if i['category'] == category]
    return items

@router.post("/store/purchase")
async def purchase_store_item(request: dict, current_user: dict = Depends(get_current_user)):
    """Purchase a store item (MOCK payment - real payment integration pending)"""
    item_id = request.get('item_id')
    payment_method = request.get('payment_method', 'credit_card')  # credit_card, paypal

    # Find the item
    item = next((i for i in STORE_ITEMS if i['id'] == item_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado na loja")

    user = await db.users.find_one({"id": current_user['id']})
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    # ============ MOCK PAYMENT ============
    # In production, this would integrate with Stripe/payment processor
    # For now, we simulate a successful payment
    payment_success = True
    transaction_id = f"MOCK_{uuid.uuid4().hex[:12].upper()}"
    # ======================================

    if not payment_success:
        raise HTTPException(status_code=402, detail="Falha no pagamento")

    # Record purchase
    purchase = {
        "id": str(uuid.uuid4()),
        "user_id": current_user['id'],
        "item_id": item_id,
        "item_name": item['name'],
        "category": item['category'],
        "price_brl": item['price_brl'],
        "payment_method": payment_method,
        "transaction_id": transaction_id,
        "status": "completed",
        "created_at": datetime.utcnow(),
    }
    await db.store_purchases.insert_one(purchase)

    reward = item['game_reward']
    update_ops: dict = {}
    messages = []

    # Apply reward based on category
    if 'money' in reward:
        new_money = user['money'] + reward['money']
        update_ops['money'] = new_money
        messages.append(f"+$ {reward['money']:,.0f} adicionados à sua conta!")

    if 'xp' in reward:
        new_xp = user.get('experience_points', 0) + reward['xp']
        new_level = (new_xp // 1000) + 1
        update_ops['experience_points'] = new_xp
        update_ops['level'] = new_level
        messages.append(f"+{reward['xp']:,} XP! Agora nível {new_level}")

    if 'earnings_multiplier' in reward:
        now = datetime.utcnow()
        duration_hours = reward.get('duration_hours', 1)
        expires_at = now + timedelta(hours=duration_hours)

        # Set or update ad boost with the purchased multiplier
        existing_boost = await db.ad_boosts.find_one({"user_id": current_user['id']})
        if existing_boost:
            # Stack: use the higher multiplier and extend time
            old_expires = existing_boost.get('expires_at', now)
            if isinstance(old_expires, str):
                old_expires = datetime.fromisoformat(old_expires.replace('Z', '+00:00'))
            new_expires = max(old_expires, expires_at)
            new_mult = max(existing_boost.get('multiplier', 1.0), reward['earnings_multiplier'])
            await db.ad_boosts.update_one(
                {"_id": existing_boost['_id']},
                {"$set": {"multiplier": new_mult, "expires_at": new_expires}}
            )
        else:
            boost = AdBoost(
                user_id=current_user['id'],
                multiplier=reward['earnings_multiplier'],
                ads_watched=0,
                expires_at=expires_at
            )
            await db.ad_boosts.insert_one(boost.dict())
        messages.append(f"Boost {reward['earnings_multiplier']}x ativado por {duration_hours}h!")

    # Handle ad-free subscription
    if reward.get('ad_free'):
        now = datetime.utcnow()
        duration_days = reward.get('duration_days', 30)
        expires_at = now + timedelta(days=duration_days)

        existing_sub = await db.subscriptions.find_one({"user_id": current_user['id'], "type": "ad_free"})
        if existing_sub:
            old_expires = existing_sub.get('expires_at', now)
            if isinstance(old_expires, str):
                old_expires = datetime.fromisoformat(old_expires.replace('Z', '+00:00'))
            # Extend from current expiry if still active
            base = max(old_expires, now)
            new_expires = base + timedelta(days=duration_days)
            await db.subscriptions.update_one(
                {"_id": existing_sub['_id']},
                {"$set": {"expires_at": new_expires, "updated_at": now}}
            )
        else:
            await db.subscriptions.insert_one({
                "id": str(uuid.uuid4()),
                "user_id": current_user['id'],
                "type": "ad_free",
                "active": True,
                "expires_at": expires_at,
                "created_at": now,
                "updated_at": now,
            })
        messages.append(f"Sem Propagandas ativado por {duration_days} dias!")

    if update_ops:
        await db.users.update_one({"id": current_user['id']}, {"$set": update_ops})

    return {
        "success": True,
        "message": " | ".join(messages),
        "item": item['name'],
        "transaction_id": transaction_id,
        "payment_method": payment_method,
        "price_brl": item['price_brl'],
        "rewards_applied": reward,
        "mock_payment": True,  # Flag to indicate payment is simulated
    }

@router.get("/store/purchases")
async def get_store_purchases(current_user: dict = Depends(get_current_user)):
    """Get user's purchase history"""
    purchases = await db.store_purchases.find(
        {"user_id": current_user['id']}
    ).sort("created_at", -1).to_list(50)
    for p in purchases:
        if '_id' in p:
            del p['_id']
        if isinstance(p.get('created_at'), datetime):
            p['created_at'] = p['created_at'].isoformat()
    return purchases


# ==================== AD-FREE SUBSCRIPTION STATUS ====================

@router.get("/store/subscription-status")
async def get_subscription_status(current_user: dict = Depends(get_current_user)):
    """Check if user has active ad-free subscription"""
    now = datetime.utcnow()
    sub = await db.subscriptions.find_one({
        "user_id": current_user['id'],
        "type": "ad_free"
    })
    
    if not sub:
        return {"ad_free": False, "expires_at": None, "days_remaining": 0}
    
    expires_at = sub.get('expires_at', now)
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
    
    is_active = expires_at > now
    days_remaining = max(0, (expires_at - now).days) if is_active else 0
    
    return {
        "ad_free": is_active,
        "expires_at": expires_at.isoformat() if is_active else None,
        "days_remaining": days_remaining,
    }

# ==================== DAILY FREE MONEY (PROPAGANDA DIÁRIA) ====================

@router.post("/store/daily-reward")
async def claim_daily_reward(current_user: dict = Depends(get_current_user)):
    """Claim daily free money by watching an ad (once per day)"""
    now = datetime.utcnow()
    today = now.strftime("%Y-%m-%d")
    
    # Check if already claimed today
    existing = await db.daily_rewards.find_one({
        "user_id": current_user['id'],
        "date": today
    })
    if existing:
        raise HTTPException(status_code=400, detail="Você já resgatou sua recompensa diária hoje! Volte amanhã.")
    
    # Calculate reward based on level (higher levels get more)
    user = await db.users.find_one({"id": current_user['id']})
    user_level = user.get('level', 1)
    base_reward = 500
    reward_amount = base_reward + (user_level * 100)  # 500 + 100 per level
    
    # Record claim
    await db.daily_rewards.insert_one({
        "user_id": current_user['id'],
        "date": today,
        "amount": reward_amount,
        "created_at": now
    })
    
    # Add money
    new_money = user.get('money', 0) + reward_amount
    await db.users.update_one(
        {"id": current_user['id']},
        {"$set": {"money": new_money}}
    )
    
    return {
        "success": True,
        "message": f"Propaganda assistida! Você ganhou $ {reward_amount:,.0f}!",
        "amount": reward_amount,
        "new_balance": round(new_money, 2),
        "level_bonus": user_level * 100,
    }

@router.get("/store/daily-reward-status")
async def daily_reward_status(current_user: dict = Depends(get_current_user)):
    """Check if daily reward is available"""
    today = datetime.utcnow().strftime("%Y-%m-%d")
    existing = await db.daily_rewards.find_one({
        "user_id": current_user['id'],
        "date": today
    })
    user = await db.users.find_one({"id": current_user['id']})
    user_level = user.get('level', 1)
    reward_amount = 500 + (user_level * 100)
    
    return {
        "available": existing is None,
        "already_claimed": existing is not None,
        "reward_amount": reward_amount,
        "doubled": existing.get('doubled', False) if existing else False,
    }

@router.post("/store/double-daily")
async def double_daily_reward(current_user: dict = Depends(get_current_user)):
    """Double today's daily reward by watching an ad."""
    today = datetime.utcnow().strftime("%Y-%m-%d")
    
    existing = await db.daily_rewards.find_one({
        "user_id": current_user['id'],
        "date": today
    })
    if not existing:
        raise HTTPException(status_code=400, detail="Resgate sua recompensa diária primeiro!")
    if existing.get('doubled'):
        raise HTTPException(status_code=400, detail="Recompensa já foi dobrada hoje!")
    
    # Double the reward
    original_amount = existing.get('amount', 500)
    user = await db.users.find_one({"id": current_user['id']})
    new_money = user.get('money', 0) + original_amount
    
    await db.users.update_one(
        {"id": current_user['id']},
        {"$set": {"money": new_money}}
    )
    await db.daily_rewards.update_one(
        {"_id": existing['_id']},
        {"$set": {"doubled": True, "double_amount": original_amount}}
    )
    
    return {
        "success": True,
        "message": f"Recompensa dobrada! +$ {original_amount:,.0f} extras!",
        "bonus_amount": original_amount,
        "new_balance": round(new_money, 2),
    }



# ==================== STRIPE PAYMENTS ====================
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

@router.post("/payments/create-intent")
async def create_payment_intent(data: dict, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Create a Stripe PaymentIntent for store purchases."""
    user = await get_current_user(credentials)
    amount = data.get('amount')  # Amount in cents
    item_id = data.get('item_id')
    item_name = data.get('item_name', 'BizRealms Store Item')
    
    if not amount or amount < 100:  # Minimum $1.00
        raise HTTPException(status_code=400, detail="Invalid amount")
    
    try:
        intent = stripe.PaymentIntent.create(
            amount=int(amount),
            currency=data.get('currency', 'brl'),
            metadata={
                'user_id': user['id'],
                'item_id': str(item_id),
                'item_name': item_name,
            },
            description=f"BizRealms: {item_name}",
        )
        return {
            "client_secret": intent.client_secret,
            "payment_intent_id": intent.id,
        }
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/payments/confirm")
async def confirm_payment(data: dict, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Confirm a payment and deliver the purchased item."""
    user = await get_current_user(credentials)
    payment_intent_id = data.get('payment_intent_id')
    
    if not payment_intent_id:
        raise HTTPException(status_code=400, detail="Payment intent ID required")
    
    try:
        intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        
        if intent.status == 'succeeded':
            item_id = intent.metadata.get('item_id')
            item_name = intent.metadata.get('item_name')
            amount = intent.amount
            
            # Record purchase
            await db.purchases.insert_one({
                'user_id': user['id'],
                'payment_intent_id': payment_intent_id,
                'item_id': item_id,
                'item_name': item_name,
                'amount': amount,
                'currency': intent.currency,
                'status': 'completed',
                'created_at': datetime.utcnow(),
            })
            
            # Add notification
            await db.notifications.insert_one({
                'user_id': user['id'],
                'type': 'purchase',
                'title': f'Purchase Confirmed',
                'message': f'{item_name} has been added to your account!',
                'icon': 'cart',
                'read': False,
                'created_at': datetime.utcnow(),
            })
            
            return {"status": "success", "message": f"Purchase of {item_name} confirmed!"}
        else:
            return {"status": intent.status, "message": "Payment not yet completed"}
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/payments/history")
async def payment_history(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get user's payment history."""
    user = await get_current_user(credentials)
    purchases = await db.purchases.find({'user_id': user['id']}).sort('created_at', -1).to_list(50)
    for p in purchases:
        p.pop('_id', None)
        p['created_at'] = p['created_at'].isoformat() if isinstance(p.get('created_at'), datetime) else str(p.get('created_at', ''))
    return {"purchases": purchases}

@router.post("/payments/create-checkout-session")
async def create_checkout_session(data: dict, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Create a Stripe Checkout Session for a store item."""
    user = await get_current_user(credentials)
    item_id = data.get('item_id')
    
    # Find item in store
    item = next((i for i in STORE_ITEMS if i['id'] == item_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    
    # Price in centavos (BRL uses centavos)
    price_cents = int(item['price_brl'] * 100)
    
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'brl',
                    'product_data': {
                        'name': item['name'],
                        'description': item.get('description', ''),
                    },
                    'unit_amount': price_cents,
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url='https://bizrealms.app/payment-success?session_id={CHECKOUT_SESSION_ID}',
            cancel_url='https://bizrealms.app/payment-cancel',
            metadata={
                'user_id': user['id'],
                'item_id': item_id,
                'item_name': item['name'],
            },
        )
        return {
            "session_id": session.id,
            "checkout_url": session.url,
        }
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/payments/check-session")
async def check_session_status(data: dict, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Check Stripe session status and deliver item if paid."""
    user = await get_current_user(credentials)
    session_id = data.get('session_id')
    
    if not session_id:
        raise HTTPException(status_code=400, detail="Session ID required")
    
    try:
        session = stripe.checkout.Session.retrieve(session_id)
        
        if session.payment_status == 'paid':
            # Check if already processed
            existing = await db.store_purchases.find_one({'stripe_session_id': session_id})
            if existing:
                return {"status": "already_processed", "message": "Compra já foi processada!"}
            
            item_id = session.metadata.get('item_id')
            item_name = session.metadata.get('item_name')
            user_id = session.metadata.get('user_id')
            
            # Verify user matches
            if user_id != user['id']:
                raise HTTPException(status_code=403, detail="Sessão não pertence a este usuário")
            
            # Find item
            item = next((i for i in STORE_ITEMS if i['id'] == item_id), None)
            if not item:
                raise HTTPException(status_code=404, detail="Item não encontrado")
            
            # Record purchase
            purchase = {
                "id": str(uuid.uuid4()),
                "user_id": user['id'],
                "item_id": item_id,
                "item_name": item['name'],
                "category": item['category'],
                "price_brl": item['price_brl'],
                "payment_method": "stripe",
                "stripe_session_id": session_id,
                "transaction_id": session.payment_intent or session.id,
                "status": "completed",
                "created_at": datetime.utcnow(),
            }
            await db.store_purchases.insert_one(purchase)
            
            # Deliver item rewards
            reward = item.get('game_reward', {})
            update_ops = {}
            message_parts = []
            
            if reward.get('money'):
                update_ops['$inc'] = update_ops.get('$inc', {})
                update_ops['$inc']['money'] = reward['money']
                message_parts.append(f"+$ {reward['money']:,.0f}")
            
            if reward.get('xp'):
                update_ops['$inc'] = update_ops.get('$inc', {})
                update_ops['$inc']['experience_points'] = reward['xp']
                message_parts.append(f"+{reward['xp']:,.0f} XP")
            
            if update_ops:
                await db.users.update_one({'id': user['id']}, update_ops)
            
            # Handle earnings boost
            if reward.get('earnings_multiplier'):
                boost_end = datetime.utcnow() + timedelta(hours=reward['duration_hours'])
                await db.ad_boosts.update_one(
                    {'user_id': user['id']},
                    {'$set': {
                        'multiplier': reward['earnings_multiplier'],
                        'expires_at': boost_end,
                        'active': True,
                    }},
                    upsert=True
                )
                message_parts.append(f"{reward['earnings_multiplier']}x por {reward['duration_hours']}h")
            
            # Add notification
            await db.notifications.insert_one({
                'user_id': user['id'],
                'type': 'purchase',
                'title': 'Compra Confirmada!',
                'message': f'{item_name} — {", ".join(message_parts)}',
                'icon': 'cart',
                'read': False,
                'created_at': datetime.utcnow(),
            })
            
            return {
                "status": "paid",
                "message": f"Compra confirmada! {', '.join(message_parts)}",
                "item_name": item_name,
            }
        elif session.payment_status == 'unpaid':
            return {"status": "unpaid", "message": "Pagamento pendente"}
        else:
            return {"status": session.payment_status, "message": "Status do pagamento: " + session.payment_status}
    
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))

