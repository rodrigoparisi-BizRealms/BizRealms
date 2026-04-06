"""BizRealms - Bank Routes."""
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


router = APIRouter()

# ==================== BANCO ONLINE ====================

# --- Credit Card ---
@router.get("/bank/account")
async def get_bank_account(current_user: dict = Depends(get_current_user)):
    """Get full bank account overview"""
    user = await db.users.find_one({"id": current_user['id']})
    card = await db.credit_cards.find_one({"user_id": current_user['id']})
    if not card:
        # Auto-create credit card on first access
        limit = 5000 + (user.get('level', 1) * 1000)
        card = {
            "id": str(uuid.uuid4()),
            "user_id": current_user['id'],
            "card_number": f"**** **** **** {str(uuid.uuid4().int)[:4]}",
            "limit": limit,
            "balance_used": 0,
            "miles_points": 0,
            "created_at": datetime.utcnow(),
        }
        await db.credit_cards.insert_one(card)
    
    loans = await db.loans.find({"user_id": current_user['id'], "status": {"$ne": "paid_off"}}).to_list(20)
    for l in loans:
        if '_id' in l: del l['_id']
        for k in ['created_at', 'next_payment_date']:
            if isinstance(l.get(k), datetime): l[k] = l[k].isoformat()

    total_debt = sum(l.get('remaining_balance', 0) for l in loans)
    
    # Miles redemption catalog
    trips = [
        {"id": "trip_nacional", "name": "Viagem Nacional", "description": "Passagem aérea ida e volta", "miles_cost": 5000, "xp_reward": 2000, "icon": "airplane"},
        {"id": "trip_latam", "name": "Viagem América Latina", "description": "Passagem + 3 noites hotel", "miles_cost": 15000, "xp_reward": 5000, "icon": "earth"},
        {"id": "trip_europa", "name": "Viagem Europa", "description": "Passagem + 5 noites hotel de luxo", "miles_cost": 40000, "xp_reward": 15000, "icon": "globe"},
        {"id": "trip_mundo", "name": "Volta ao Mundo", "description": "Tour completo por 5 países", "miles_cost": 100000, "xp_reward": 50000, "icon": "planet"},
    ]

    if '_id' in card: del card['_id']
    if isinstance(card.get('created_at'), datetime): card['created_at'] = card['created_at'].isoformat()

    return {
        "balance": round(user.get('money', 0), 2),
        "level": user.get('level', 1),
        "credit_card": card,
        "loans": loans,
        "total_debt": round(total_debt, 2),
        "available_trips": trips,
        "loan_limits": {
            "small_no_guarantee": min(50000, 5000 + user.get('level', 1) * 2000),
            "large_with_guarantee": 500000,
        }
    }


@router.post("/bank/credit-card/purchase")
async def credit_card_purchase(request: dict, current_user: dict = Depends(get_current_user)):
    """Make a credit card purchase (generates miles)"""
    amount = request.get('amount', 0)
    description = request.get('description', 'Compra')
    
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Valor inválido")

    card = await db.credit_cards.find_one({"user_id": current_user['id']})
    if not card:
        raise HTTPException(status_code=404, detail="Cartão não encontrado")
    
    available = card['limit'] - card.get('balance_used', 0)
    if amount > available:
        raise HTTPException(status_code=400, detail=f"Limite insuficiente. Disponível: $ {available:,.2f}")
    
    # 1 mile per $ 1 spent
    miles_earned = int(amount)
    
    await db.credit_cards.update_one(
        {"_id": card['_id']},
        {"$inc": {"balance_used": amount, "miles_points": miles_earned}}
    )

    # Record transaction
    await db.card_transactions.insert_one({
        "user_id": current_user['id'],
        "amount": amount,
        "description": description,
        "miles_earned": miles_earned,
        "created_at": datetime.utcnow(),
    })

    return {
        "success": True,
        "message": f"Compra de $ {amount:,.2f} realizada! +{miles_earned} milhas",
        "miles_earned": miles_earned,
        "total_miles": card.get('miles_points', 0) + miles_earned,
        "balance_used": card.get('balance_used', 0) + amount,
    }


@router.post("/bank/credit-card/pay-bill")
async def pay_credit_card_bill(request: dict, current_user: dict = Depends(get_current_user)):
    """Pay credit card bill (partially or fully)"""
    amount = request.get('amount', 0)
    
    card = await db.credit_cards.find_one({"user_id": current_user['id']})
    if not card:
        raise HTTPException(status_code=404, detail="Cartão não encontrado")
    
    balance_used = card.get('balance_used', 0)
    if amount <= 0 or amount > balance_used:
        amount = balance_used
    
    user = await db.users.find_one({"id": current_user['id']})
    if user['money'] < amount:
        raise HTTPException(status_code=400, detail="Saldo insuficiente para pagar a fatura")
    
    await db.users.update_one({"id": current_user['id']}, {"$inc": {"money": -amount}})
    await db.credit_cards.update_one({"_id": card['_id']}, {"$inc": {"balance_used": -amount}})
    
    return {
        "success": True,
        "message": f"Fatura de $ {amount:,.2f} paga com sucesso!",
        "new_balance": round(user['money'] - amount, 2),
        "remaining_bill": round(balance_used - amount, 2),
    }


@router.post("/bank/credit-card/redeem-miles")
async def redeem_miles(request: dict, current_user: dict = Depends(get_current_user)):
    """Redeem miles for trips (XP reward)"""
    trip_id = request.get('trip_id')
    
    trips_catalog = {
        "trip_nacional": {"miles_cost": 5000, "xp_reward": 2000, "name": "Viagem Nacional"},
        "trip_latam": {"miles_cost": 15000, "xp_reward": 5000, "name": "Viagem América Latina"},
        "trip_europa": {"miles_cost": 40000, "xp_reward": 15000, "name": "Viagem Europa"},
        "trip_mundo": {"miles_cost": 100000, "xp_reward": 50000, "name": "Volta ao Mundo"},
    }
    
    trip = trips_catalog.get(trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Viagem não encontrada")
    
    card = await db.credit_cards.find_one({"user_id": current_user['id']})
    if not card or card.get('miles_points', 0) < trip['miles_cost']:
        raise HTTPException(status_code=400, detail=f"Milhas insuficientes. Necessário: {trip['miles_cost']}")
    
    user = await db.users.find_one({"id": current_user['id']})
    new_xp = user.get('experience_points', 0) + trip['xp_reward']
    new_level = (new_xp // 1000) + 1
    
    await db.credit_cards.update_one({"_id": card['_id']}, {"$inc": {"miles_points": -trip['miles_cost']}})
    await db.users.update_one({"id": current_user['id']}, {"$set": {"experience_points": new_xp, "level": new_level}})
    
    return {
        "success": True,
        "message": f"{trip['name']} resgatada! +{trip['xp_reward']} XP! Agora nível {new_level}",
        "trip_name": trip['name'],
        "xp_gained": trip['xp_reward'],
        "miles_spent": trip['miles_cost'],
        "remaining_miles": card.get('miles_points', 0) - trip['miles_cost'],
    }


# --- Loans ---
@router.post("/bank/loan/apply")
async def apply_for_loan(request: dict, current_user: dict = Depends(get_current_user)):
    """Apply for a loan"""
    amount = request.get('amount', 0)
    loan_type = request.get('type', 'small')  # small or large
    guarantee_asset_id = request.get('guarantee_asset_id')
    months = request.get('months', 12)
    
    user = await db.users.find_one({"id": current_user['id']})
    user_level = user.get('level', 1)
    
    # Check existing unpaid loans count
    active_loans = await db.loans.count_documents({"user_id": current_user['id'], "status": "active"})
    if active_loans >= 3:
        raise HTTPException(status_code=400, detail="Limite de 3 empréstimos ativos atingido")
    
    if loan_type == 'small':
        max_amount = min(50000, 5000 + user_level * 2000)
        if amount > max_amount:
            raise HTTPException(status_code=400, detail=f"Valor máximo sem garantia: $ {max_amount:,.0f}")
        interest_rate = 0.035  # 3.5% monthly
        months = min(months, 24)
    else:
        # Large loan requires guarantee (asset)
        if not guarantee_asset_id:
            raise HTTPException(status_code=400, detail="Empréstimo grande requer garantia (bem)")
        asset = await db.user_assets.find_one({"id": guarantee_asset_id, "user_id": current_user['id']})
        if not asset:
            raise HTTPException(status_code=400, detail="Bem de garantia não encontrado")
        max_amount = min(500000, asset.get('purchase_price', 0) * 0.8)
        if amount > max_amount:
            raise HTTPException(status_code=400, detail=f"Valor máximo com esta garantia: $ {max_amount:,.0f}")
        interest_rate = 0.02  # 2% monthly (lower with guarantee)
        months = min(months, 60)
    
    if amount <= 0 or months <= 0:
        raise HTTPException(status_code=400, detail="Valores inválidos")
    
    total_with_interest = amount * ((1 + interest_rate) ** months)
    monthly_payment = round(total_with_interest / months, 2)
    discount_payoff = round(amount * 1.05, 2)  # 5% above principal for early payoff
    
    loan = {
        "id": str(uuid.uuid4()),
        "user_id": current_user['id'],
        "amount": amount,
        "type": loan_type,
        "interest_rate": interest_rate,
        "months": months,
        "monthly_payment": monthly_payment,
        "total_with_interest": round(total_with_interest, 2),
        "remaining_balance": round(total_with_interest, 2),
        "payments_made": 0,
        "guarantee_asset_id": guarantee_asset_id,
        "discount_payoff": discount_payoff,
        "status": "active",
        "created_at": datetime.utcnow(),
        "next_payment_date": (datetime.utcnow() + timedelta(days=30)).isoformat(),
    }
    await db.loans.insert_one(loan)
    
    # Credit money to user
    new_money = user['money'] + amount
    await db.users.update_one({"id": current_user['id']}, {"$set": {"money": new_money}})
    
    return {
        "success": True,
        "message": f"Empréstimo de $ {amount:,.0f} aprovado! Parcela: $ {monthly_payment:,.2f}/mês",
        "loan_id": loan['id'],
        "monthly_payment": monthly_payment,
        "total_with_interest": round(total_with_interest, 2),
        "months": months,
        "new_balance": round(new_money, 2),
    }


@router.post("/bank/loan/pay")
async def pay_loan_installment(request: dict, current_user: dict = Depends(get_current_user)):
    """Make a monthly loan payment"""
    loan_id = request.get('loan_id')
    
    loan = await db.loans.find_one({"id": loan_id, "user_id": current_user['id'], "status": "active"})
    if not loan:
        raise HTTPException(status_code=404, detail="Empréstimo não encontrado")
    
    payment = loan['monthly_payment']
    user = await db.users.find_one({"id": current_user['id']})
    if user['money'] < payment:
        raise HTTPException(status_code=400, detail=f"Saldo insuficiente. Parcela: $ {payment:,.2f}")
    
    new_remaining = max(0, loan['remaining_balance'] - payment)
    new_payments = loan['payments_made'] + 1
    status = "paid_off" if new_remaining <= 0 else "active"
    
    await db.loans.update_one({"_id": loan['_id']}, {"$set": {
        "remaining_balance": round(new_remaining, 2),
        "payments_made": new_payments,
        "status": status,
        "next_payment_date": (datetime.utcnow() + timedelta(days=30)).isoformat() if status == "active" else None,
    }})
    await db.users.update_one({"id": current_user['id']}, {"$inc": {"money": -payment}})
    
    msg = f"Parcela {new_payments}/{loan['months']} paga! $ {payment:,.2f}"
    if status == "paid_off":
        msg = "Empréstimo quitado! Parabéns!"
    
    return {
        "success": True,
        "message": msg,
        "payment_number": new_payments,
        "remaining_balance": round(new_remaining, 2),
        "status": status,
        "new_balance": round(user['money'] - payment, 2),
    }


@router.post("/bank/loan/payoff")
async def payoff_loan(request: dict, current_user: dict = Depends(get_current_user)):
    """Pay off entire loan with discount"""
    loan_id = request.get('loan_id')
    
    loan = await db.loans.find_one({"id": loan_id, "user_id": current_user['id'], "status": "active"})
    if not loan:
        raise HTTPException(status_code=404, detail="Empréstimo não encontrado")
    
    payoff_amount = loan.get('discount_payoff', loan['remaining_balance'])
    # If already paid more than discount amount, use remaining
    payoff_amount = min(payoff_amount, loan['remaining_balance'])
    savings = loan['remaining_balance'] - payoff_amount
    
    user = await db.users.find_one({"id": current_user['id']})
    if user['money'] < payoff_amount:
        raise HTTPException(status_code=400, detail=f"Saldo insuficiente. Valor de quitação: $ {payoff_amount:,.2f}")
    
    await db.loans.update_one({"_id": loan['_id']}, {"$set": {
        "remaining_balance": 0,
        "status": "paid_off",
    }})
    await db.users.update_one({"id": current_user['id']}, {"$inc": {"money": -payoff_amount}})
    
    return {
        "success": True,
        "message": f"Empréstimo quitado com desconto! Economia: $ {savings:,.2f}",
        "payoff_amount": round(payoff_amount, 2),
        "savings": round(savings, 2),
        "new_balance": round(user['money'] - payoff_amount, 2),
    }



