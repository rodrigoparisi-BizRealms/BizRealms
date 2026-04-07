"""BizRealms - Investments Routes."""
import logging
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
logger = logging.getLogger(__name__)

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
    currency: str = "USD"
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
    # World Stocks (fictional names inspired by real companies)
    {"ticker": "TVST", "name": "TechVista Inc.", "category": "stocks", "base_price": 195.00, "volatility": 2.0, "trend": 0.06, "description": "Global tech leader in smartphones and software", "sector": "Technology", "market_cap": "$ 3T"},
    {"ticker": "NVCP", "name": "NovaCorp", "category": "stocks", "base_price": 178.00, "volatility": 2.2, "trend": 0.05, "description": "Search engine and cloud computing giant", "sector": "Technology", "market_cap": "$ 2T"},
    {"ticker": "BSHL", "name": "BlueShield Systems", "category": "stocks", "base_price": 430.00, "volatility": 1.8, "trend": 0.04, "description": "Enterprise software and cloud platforms", "sector": "Technology", "market_cap": "$ 2.8T"},
    {"ticker": "AMZX", "name": "AmazoTech", "category": "stocks", "base_price": 185.00, "volatility": 2.5, "trend": 0.05, "description": "E-commerce and cloud infrastructure", "sector": "E-Commerce", "market_cap": "$ 1.9T"},
    {"ticker": "TSLE", "name": "TeslaWave Motors", "category": "stocks", "base_price": 250.00, "volatility": 4.0, "trend": 0.08, "description": "Electric vehicles and clean energy", "sector": "Automotive", "market_cap": "$ 800B"},
    {"ticker": "NVDX", "name": "NeuraVida Chips", "category": "stocks", "base_price": 130.00, "volatility": 3.5, "trend": 0.10, "description": "AI chips and GPU computing leader", "sector": "Semiconductors", "market_cap": "$ 3.2T"},
    {"ticker": "METV", "name": "MetaVerse Platforms", "category": "stocks", "base_price": 510.00, "volatility": 2.8, "trend": 0.04, "description": "Social media and virtual reality", "sector": "Social Media", "market_cap": "$ 1.3T"},
    {"ticker": "JPFN", "name": "JP Financial Group", "category": "stocks", "base_price": 205.00, "volatility": 1.5, "trend": 0.03, "description": "Investment banking and financial services", "sector": "Finance", "market_cap": "$ 600B"},
    {"ticker": "WDIS", "name": "WonderLand Entertainment", "category": "stocks", "base_price": 112.00, "volatility": 2.0, "trend": 0.02, "description": "Global entertainment and streaming", "sector": "Entertainment", "market_cap": "$ 200B"},
    {"ticker": "JNJH", "name": "JNJ HealthCorp", "category": "stocks", "base_price": 155.00, "volatility": 1.2, "trend": 0.02, "description": "Pharmaceutical and healthcare giant", "sector": "Healthcare", "market_cap": "$ 400B"},
    {"ticker": "COCA", "name": "CocaBrew International", "category": "stocks", "base_price": 62.00, "volatility": 1.0, "trend": 0.01, "description": "World's largest beverage company", "sector": "Beverages", "market_cap": "$ 260B"},
    {"ticker": "NKSP", "name": "NikeSport Global", "category": "stocks", "base_price": 78.00, "volatility": 2.0, "trend": 0.03, "description": "Athletic footwear and apparel", "sector": "Consumer Goods", "market_cap": "$ 120B"},
    # Crypto
    {"ticker": "BTC", "name": "Bitcoin", "category": "crypto", "base_price": 67500.00, "volatility": 4.0, "trend": 0.08, "description": "The largest cryptocurrency by market cap", "market_cap": "$ 1.3T"},
    {"ticker": "ETH", "name": "Ethereum", "category": "crypto", "base_price": 3500.00, "volatility": 5.0, "trend": 0.06, "description": "Smart contract platform", "market_cap": "$ 400B"},
    {"ticker": "SOL", "name": "Solana", "category": "crypto", "base_price": 175.00, "volatility": 6.5, "trend": 0.10, "description": "High performance blockchain", "market_cap": "$ 80B"},
    {"ticker": "BNB", "name": "Binance Coin", "category": "crypto", "base_price": 620.00, "volatility": 4.5, "trend": 0.04, "description": "Binance native token", "market_cap": "$ 90B"},
    {"ticker": "ADA", "name": "Cardano", "category": "crypto", "base_price": 0.75, "volatility": 7.0, "trend": -0.03, "description": "Proof-of-stake blockchain", "market_cap": "$ 25B"},
    # ETFs / Funds
    {"ticker": "SPYF", "name": "S&P 500 Fund", "category": "funds", "base_price": 520.00, "volatility": 1.0, "trend": 0.04, "description": "Tracks the S&P 500 index", "sector": "Index Fund"},
    {"ticker": "QQFN", "name": "Nasdaq Tech Fund", "category": "funds", "base_price": 430.00, "volatility": 1.5, "trend": 0.05, "description": "Tracks top 100 tech companies", "sector": "Tech Fund"},
    {"ticker": "REIT", "name": "Global REIT Fund", "category": "funds", "base_price": 85.00, "volatility": 0.8, "trend": 0.03, "description": "Real estate investment trust fund", "sector": "Real Estate"},
    {"ticker": "BOND", "name": "US Treasury Bond Fund", "category": "funds", "base_price": 100.00, "volatility": 0.3, "trend": 0.01, "description": "Safe government bond fund", "sector": "Fixed Income"},
    # Commodities
    {"ticker": "GOLD", "name": "Gold", "category": "commodities", "base_price": 2350.00, "volatility": 1.5, "trend": 0.05, "description": "Troy ounce of gold", "currency": "USD"},
    {"ticker": "SLVR", "name": "Silver", "category": "commodities", "base_price": 29.50, "volatility": 2.0, "trend": 0.03, "description": "Troy ounce of silver", "currency": "USD"},
    {"ticker": "OIL", "name": "Crude Oil (Brent)", "category": "commodities", "base_price": 82.00, "volatility": 3.0, "trend": -0.02, "description": "Barrel of Brent crude oil", "currency": "USD"},
    {"ticker": "CORN", "name": "Corn", "category": "commodities", "base_price": 4.50, "volatility": 2.5, "trend": 0.01, "description": "Bushel of corn", "currency": "USD"},
    {"ticker": "COFE", "name": "Coffee Arabica", "category": "commodities", "base_price": 2.40, "volatility": 3.5, "trend": 0.04, "description": "Pound of arabica coffee", "currency": "USD"},
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
    """Seed investment assets - reseed to update"""
    await db.investment_assets.delete_many({})
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
        else:
            # Fallback: use avg_price if asset not found
            current_price = h.get('avg_price', 0)
        
        invested = h.get('quantity', 0) * h.get('avg_price', 0)
        current_value = h.get('quantity', 0) * current_price
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


