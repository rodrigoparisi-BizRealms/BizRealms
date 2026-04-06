"""BizRealms - Investments Routes."""
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional
from datetime import datetime, timedelta
from bson import ObjectId
import uuid
import random
import math
import hashlib

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

# ==================== INVESTMENT SYSTEM ====================

# Investment Models
class InvestmentAsset(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    ticker: str
    name: str
    category: str  # "acoes", "crypto", "fundos", "commodities"
    base_price: float
    current_price: float
    volatility: float  # Daily volatility as percentage (e.g., 2.0 = 2%)
    trend: float  # Drift: positive = bullish, negative = bearish
    description: str
    currency: str = "BRL"
    market_cap: Optional[str] = None
    sector: Optional[str] = None

class BuyRequest(BaseModel):
    asset_id: str
    quantity: float

class SellRequest(BaseModel):
    asset_id: str
    quantity: float

# Seed Investment Assets
INVESTMENT_SEEDS = [
    # Ações B3
    {"ticker": "PETR4", "name": "Petrobras PN", "category": "acoes", "base_price": 38.50, "volatility": 2.5, "trend": 0.05, "description": "Petróleo Brasileiro S.A. - Ação preferencial", "sector": "Petróleo & Gás", "market_cap": "$ 500B"},
    {"ticker": "VALE3", "name": "Vale ON", "category": "acoes", "base_price": 62.00, "volatility": 2.8, "trend": 0.03, "description": "Vale S.A. - Mineração e metais", "sector": "Mineração", "market_cap": "$ 280B"},
    {"ticker": "ITUB4", "name": "Itaú Unibanco PN", "category": "acoes", "base_price": 32.00, "volatility": 1.8, "trend": 0.04, "description": "Itaú Unibanco - Maior banco privado do Brasil", "sector": "Financeiro", "market_cap": "$ 300B"},
    {"ticker": "BBDC4", "name": "Bradesco PN", "category": "acoes", "base_price": 14.50, "volatility": 2.2, "trend": -0.02, "description": "Banco Bradesco S.A.", "sector": "Financeiro", "market_cap": "$ 150B"},
    {"ticker": "WEGE3", "name": "WEG ON", "category": "acoes", "base_price": 44.00, "volatility": 2.0, "trend": 0.06, "description": "WEG S.A. - Motores e equipamentos elétricos", "sector": "Industrial", "market_cap": "$ 185B"},
    {"ticker": "MGLU3", "name": "Magazine Luiza ON", "category": "acoes", "base_price": 2.80, "volatility": 5.0, "trend": -0.08, "description": "Magazine Luiza - E-commerce e varejo", "sector": "Varejo", "market_cap": "$ 18B"},
    {"ticker": "ABEV3", "name": "Ambev ON", "category": "acoes", "base_price": 13.20, "volatility": 1.5, "trend": 0.02, "description": "Ambev S.A. - Maior cervejaria da América Latina", "sector": "Bebidas", "market_cap": "$ 210B"},
    {"ticker": "B3SA3", "name": "B3 ON", "category": "acoes", "base_price": 12.50, "volatility": 2.3, "trend": 0.01, "description": "B3 S.A. - Bolsa de Valores do Brasil", "sector": "Financeiro", "market_cap": "$ 70B"},
    # Crypto
    {"ticker": "BTC", "name": "Bitcoin", "category": "crypto", "base_price": 350000.00, "volatility": 4.0, "trend": 0.08, "description": "A maior criptomoeda do mundo por capitalização", "currency": "BRL", "market_cap": "US$ 1.3T"},
    {"ticker": "ETH", "name": "Ethereum", "category": "crypto", "base_price": 18500.00, "volatility": 5.0, "trend": 0.06, "description": "Plataforma de contratos inteligentes", "currency": "BRL", "market_cap": "US$ 400B"},
    {"ticker": "SOL", "name": "Solana", "category": "crypto", "base_price": 850.00, "volatility": 6.5, "trend": 0.10, "description": "Blockchain de alta performance", "currency": "BRL", "market_cap": "US$ 80B"},
    {"ticker": "BNB", "name": "Binance Coin", "category": "crypto", "base_price": 3200.00, "volatility": 4.5, "trend": 0.04, "description": "Token nativo da Binance", "currency": "BRL", "market_cap": "US$ 90B"},
    {"ticker": "ADA", "name": "Cardano", "category": "crypto", "base_price": 3.80, "volatility": 7.0, "trend": -0.03, "description": "Blockchain proof-of-stake", "currency": "BRL", "market_cap": "US$ 25B"},
    # Fundos
    {"ticker": "KNRI11", "name": "Kinea Renda Imobiliária", "category": "fundos", "base_price": 136.00, "volatility": 0.8, "trend": 0.03, "description": "Fundo imobiliário focado em renda de aluguéis", "sector": "FII - Tijolo"},
    {"ticker": "HGLG11", "name": "CSHG Logística", "category": "fundos", "base_price": 160.00, "volatility": 1.0, "trend": 0.04, "description": "FII de galpões logísticos", "sector": "FII - Logística"},
    {"ticker": "XPML11", "name": "XP Malls", "category": "fundos", "base_price": 96.00, "volatility": 1.2, "trend": 0.02, "description": "FII de shoppings centers", "sector": "FII - Shopping"},
    {"ticker": "MXRF11", "name": "Maxi Renda", "category": "fundos", "base_price": 10.50, "volatility": 0.5, "trend": 0.01, "description": "Fundo de papel - CRIs e CRAs", "sector": "FII - Papel"},
    # Commodities
    {"ticker": "OURO", "name": "Ouro", "category": "commodities", "base_price": 320.00, "volatility": 1.5, "trend": 0.05, "description": "Onça troy de ouro (g)", "currency": "BRL"},
    {"ticker": "PRATA", "name": "Prata", "category": "commodities", "base_price": 5.20, "volatility": 2.0, "trend": 0.03, "description": "Onça troy de prata (g)", "currency": "BRL"},
    {"ticker": "PETROL", "name": "Petróleo Brent", "category": "commodities", "base_price": 420.00, "volatility": 3.0, "trend": -0.02, "description": "Barril de petróleo Brent em reais", "currency": "BRL"},
    {"ticker": "SOJA", "name": "Soja", "category": "commodities", "base_price": 135.00, "volatility": 2.5, "trend": 0.01, "description": "Saca de 60kg de soja", "currency": "BRL"},
    {"ticker": "CAFE", "name": "Café Arábica", "category": "commodities", "base_price": 1420.00, "volatility": 3.5, "trend": 0.04, "description": "Saca de 60kg de café arábica", "currency": "BRL"},
]

def generate_price(base_price: float, volatility: float, trend: float, seed_val: int) -> float:
    """Generate a deterministic but realistic price based on a seed value"""
    rng = random.Random(seed_val)
    # Random walk with drift
    daily_return = trend / 100 + (volatility / 100) * rng.gauss(0, 1)
    price = base_price * (1 + daily_return)
    return max(price * 0.01, price)  # Never go below 1% of base

def generate_price_history(asset: dict, days: int = 30) -> list:
    """Generate realistic price history for an asset"""
    prices = []
    current_price = asset['base_price']
    now = datetime.utcnow()
    
    # Use asset ticker as part of the seed for consistency
    ticker_hash = int(hashlib.md5(asset['ticker'].encode()).hexdigest()[:8], 16)
    
    for i in range(days):
        day = now - timedelta(days=days - i)
        day_seed = ticker_hash + int(day.timestamp() / 86400)
        rng = random.Random(day_seed)
        
        daily_return = asset['trend'] / 100 + (asset['volatility'] / 100) * rng.gauss(0, 1)
        current_price = current_price * (1 + daily_return)
        current_price = max(asset['base_price'] * 0.3, min(asset['base_price'] * 3.0, current_price))
        
        prices.append({
            "date": day.strftime("%Y-%m-%d"),
            "price": round(current_price, 2),
            "volume": int(rng.uniform(100000, 10000000))
        })
    
    return prices

def get_current_price(asset: dict, event_multiplier: float = 1.0) -> float:
    """Get the current simulated price for an asset, applying market event effects"""
    history = generate_price_history(asset, 30)
    base = history[-1]['price'] if history else asset['base_price']
    return round(base * event_multiplier, 2)

async def seed_investments():
    """Seed investment assets if not exists"""
    count = await db.investment_assets.count_documents({})
    if count == 0:
        assets = []
        for seed in INVESTMENT_SEEDS:
            asset = {
                "id": str(uuid.uuid4()),
                **seed,
                "current_price": seed['base_price'],
                "created_at": datetime.utcnow()
            }
            asset['current_price'] = get_current_price(seed)
            assets.append(asset)
        await db.investment_assets.insert_many(assets)
        logger.info(f"Seeded {len(assets)} investment assets")


async def startup_investments():
    await seed_investments()

# Investment Endpoints
@router.get("/investments/market")
async def get_market(category: Optional[str] = None):
    """Get all investment assets with current prices, optionally filtered by category"""
    query = {}
    if category:
        query['category'] = category
    
    assets = await db.investment_assets.find(query).to_list(100)
    
    result = []
    for asset in assets:
        if '_id' in asset:
            del asset['_id']
        
        # Generate current price and daily change
        history = generate_price_history(asset, 7)
        if len(history) >= 2:
            asset['current_price'] = history[-1]['price']
            prev_price = history[-2]['price']
            change = asset['current_price'] - prev_price
            change_pct = (change / prev_price) * 100
            asset['daily_change'] = round(change, 2)
            asset['daily_change_pct'] = round(change_pct, 2)
        else:
            asset['daily_change'] = 0
            asset['daily_change_pct'] = 0
        
        # Mini sparkline data (last 7 days)
        asset['sparkline'] = [p['price'] for p in history]
        
        result.append(asset)
    
    # Update prices in DB
    for asset in result:
        await db.investment_assets.update_one(
            {"id": asset['id']},
            {"$set": {"current_price": asset['current_price']}}
        )
    
    return result

@router.get("/investments/asset/{asset_id}/history")
async def get_asset_history(asset_id: str, days: int = 30, current_user: dict = Depends(get_current_user)):
    """Get price history for a specific asset"""
    asset = await db.investment_assets.find_one({"id": asset_id})
    if not asset:
        raise HTTPException(status_code=404, detail="Ativo não encontrado")
    
    history = generate_price_history(asset, min(days, 90))
    
    if '_id' in asset:
        del asset['_id']
    
    return {
        "asset": asset,
        "history": history,
        "current_price": history[-1]['price'] if history else asset['base_price']
    }

@router.post("/investments/buy")
async def buy_asset(request: BuyRequest, current_user: dict = Depends(get_current_user)):
    """Buy an investment asset"""
    asset = await db.investment_assets.find_one({"id": request.asset_id})
    if not asset:
        raise HTTPException(status_code=404, detail="Ativo não encontrado")
    
    if request.quantity <= 0:
        raise HTTPException(status_code=400, detail="Quantidade deve ser maior que 0")
    
    # Get current price
    current_price = get_current_price(asset)
    total_cost = current_price * request.quantity
    
    # Check user funds
    user = await db.users.find_one({"id": current_user['id']})
    if user['money'] < total_cost:
        raise HTTPException(
            status_code=400, 
            detail=f"Saldo insuficiente. Necessário: $ {total_cost:.2f}, Disponível: $ {user['money']:.2f}"
        )
    
    # Deduct money
    new_money = user['money'] - total_cost
    await db.users.update_one(
        {"id": current_user['id']},
        {"$set": {"money": new_money}}
    )
    
    # Update or create holding
    existing = await db.user_holdings.find_one({
        "user_id": current_user['id'],
        "asset_id": request.asset_id
    })
    
    if existing:
        # Calculate new average price
        old_total = existing['quantity'] * existing['avg_price']
        new_total = old_total + total_cost
        new_quantity = existing['quantity'] + request.quantity
        new_avg = new_total / new_quantity
        
        await db.user_holdings.update_one(
            {"user_id": current_user['id'], "asset_id": request.asset_id},
            {"$set": {
                "quantity": new_quantity,
                "avg_price": round(new_avg, 2),
                "updated_at": datetime.utcnow()
            }}
        )
    else:
        holding = {
            "id": str(uuid.uuid4()),
            "user_id": current_user['id'],
            "asset_id": request.asset_id,
            "ticker": asset['ticker'],
            "name": asset['name'],
            "category": asset['category'],
            "quantity": request.quantity,
            "avg_price": round(current_price, 2),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        await db.user_holdings.insert_one(holding)
    
    # Record transaction
    transaction = {
        "id": str(uuid.uuid4()),
        "user_id": current_user['id'],
        "asset_id": request.asset_id,
        "ticker": asset['ticker'],
        "type": "buy",
        "quantity": request.quantity,
        "price": round(current_price, 2),
        "total": round(total_cost, 2),
        "created_at": datetime.utcnow()
    }
    await db.investment_transactions.insert_one(transaction)
    
    return {
        "message": f"Compra de {request.quantity} {asset['ticker']} realizada!",
        "ticker": asset['ticker'],
        "quantity": request.quantity,
        "price": round(current_price, 2),
        "total_cost": round(total_cost, 2),
        "new_balance": round(new_money, 2)
    }

@router.post("/investments/sell")
async def sell_asset(request: SellRequest, current_user: dict = Depends(get_current_user)):
    """Sell an investment asset"""
    asset = await db.investment_assets.find_one({"id": request.asset_id})
    if not asset:
        raise HTTPException(status_code=404, detail="Ativo não encontrado")
    
    if request.quantity <= 0:
        raise HTTPException(status_code=400, detail="Quantidade deve ser maior que 0")
    
    # Check holding
    holding = await db.user_holdings.find_one({
        "user_id": current_user['id'],
        "asset_id": request.asset_id
    })
    
    if not holding or holding['quantity'] < request.quantity:
        available = holding['quantity'] if holding else 0
        raise HTTPException(
            status_code=400,
            detail=f"Quantidade insuficiente. Disponível: {available}"
        )
    
    # Get current price
    current_price = get_current_price(asset)
    total_value = current_price * request.quantity
    profit = (current_price - holding['avg_price']) * request.quantity
    
    # Add money to user
    user = await db.users.find_one({"id": current_user['id']})
    new_money = user['money'] + total_value
    await db.users.update_one(
        {"id": current_user['id']},
        {"$set": {"money": new_money}}
    )
    
    # Update holding
    new_quantity = holding['quantity'] - request.quantity
    if new_quantity <= 0.0001:  # Essentially zero
        await db.user_holdings.delete_one({
            "user_id": current_user['id'],
            "asset_id": request.asset_id
        })
    else:
        await db.user_holdings.update_one(
            {"user_id": current_user['id'], "asset_id": request.asset_id},
            {"$set": {"quantity": new_quantity, "updated_at": datetime.utcnow()}}
        )
    
    # Record transaction
    transaction = {
        "id": str(uuid.uuid4()),
        "user_id": current_user['id'],
        "asset_id": request.asset_id,
        "ticker": asset['ticker'],
        "type": "sell",
        "quantity": request.quantity,
        "price": round(current_price, 2),
        "total": round(total_value, 2),
        "profit": round(profit, 2),
        "created_at": datetime.utcnow()
    }
    await db.investment_transactions.insert_one(transaction)
    
    profit_msg = f"Lucro: $ {profit:.2f}" if profit >= 0 else f"Prejuízo: $ {abs(profit):.2f}"
    
    return {
        "message": f"Venda de {request.quantity} {asset['ticker']} realizada!",
        "ticker": asset['ticker'],
        "quantity": request.quantity,
        "price": round(current_price, 2),
        "total_value": round(total_value, 2),
        "profit": round(profit, 2),
        "profit_message": profit_msg,
        "new_balance": round(new_money, 2)
    }

@router.get("/investments/portfolio")
async def get_portfolio(current_user: dict = Depends(get_current_user)):
    """Get user's investment portfolio"""
    holdings = await db.user_holdings.find({"user_id": current_user['id']}).to_list(100)
    
    portfolio = []
    total_invested = 0
    total_current = 0
    
    for h in holdings:
        if '_id' in h:
            del h['_id']
        
        # Get current price
        asset = await db.investment_assets.find_one({"id": h['asset_id']})
        if asset:
            current_price = get_current_price(asset)
            invested = h['quantity'] * h['avg_price']
            current_value = h['quantity'] * current_price
            profit = current_value - invested
            profit_pct = (profit / invested * 100) if invested > 0 else 0
            
            h['current_price'] = round(current_price, 2)
            h['invested'] = round(invested, 2)
            h['current_value'] = round(current_value, 2)
            h['profit'] = round(profit, 2)
            h['profit_pct'] = round(profit_pct, 2)
            
            total_invested += invested
            total_current += current_value
        
        portfolio.append(h)
    
    total_profit = total_current - total_invested
    total_profit_pct = (total_profit / total_invested * 100) if total_invested > 0 else 0
    
    return {
        "holdings": portfolio,
        "summary": {
            "total_invested": round(total_invested, 2),
            "total_current_value": round(total_current, 2),
            "total_profit": round(total_profit, 2),
            "total_profit_pct": round(total_profit_pct, 2),
            "num_positions": len(portfolio)
        }
    }

@router.get("/investments/transactions")
async def get_transactions(current_user: dict = Depends(get_current_user)):
    """Get user's investment transaction history"""
    transactions = await db.investment_transactions.find(
        {"user_id": current_user['id']}
    ).sort("created_at", -1).to_list(50)
    
    for t in transactions:
        if '_id' in t:
            del t['_id']
        if isinstance(t.get('created_at'), datetime):
            t['created_at'] = t['created_at'].isoformat()
    
    return transactions


