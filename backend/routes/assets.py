"""BizRealms - Assets Routes."""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional
from datetime import datetime, timedelta
from bson import ObjectId
import uuid
import random as _random
import math

def _generate_buyer_name():
    """Generate a random buyer name for asset offers."""
    first_names = ['Carlos', 'Maria', 'João', 'Ana', 'Pedro', 'Lucas', 'Fernanda', 'Rafael', 'Juliana', 'Diego',
                   'James', 'Emma', 'Oliver', 'Sophia', 'Liam', 'Isabella', 'Noah', 'Mia', 'Ethan', 'Ava',
                   'Hiroshi', 'Yuki', 'Chen', 'Priya', 'Ahmed', 'Fatima', 'Klaus', 'Marie', 'Paolo', 'Elena']
    last_names = ['Silva', 'Santos', 'Oliveira', 'Costa', 'Souza', 'Pereira', 'Almeida', 'Smith', 'Johnson',
                  'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Martinez', 'Anderson', 'Taylor',
                  'Tanaka', 'Müller', 'Rossi', 'Chen', 'Kim', 'Patel', 'Nguyen', 'Dubois', 'Fischer']
    return f"{_random.choice(first_names)} {_random.choice(last_names)}"


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

# ==================== ASSETS / PATRIMÔNIO SYSTEM ====================

ASSETS_FOR_SALE = [
    # Vehicles
    {"name": "Rider 160 Moto", "category": "veiculo", "subcategory": "Motos", "price": 3500, "description": "Economic motorcycle for daily commute", "appreciation": -0.05, "status_boost": 5, "level_required": 1, "icon": "bicycle"},
    {"name": "Compact City Car", "category": "veiculo", "subcategory": "Carros", "price": 8000, "description": "Affordable and fuel-efficient car", "appreciation": -0.08, "status_boost": 10, "level_required": 1, "icon": "car"},
    {"name": "Executive Sedan", "category": "veiculo", "subcategory": "Carros", "price": 28000, "description": "Comfortable executive sedan", "appreciation": -0.06, "status_boost": 25, "level_required": 3, "icon": "car"},
    {"name": "Luxor Premium SUV", "category": "veiculo", "subcategory": "SUVs", "price": 65000, "description": "Premium luxury SUV", "appreciation": -0.04, "status_boost": 50, "level_required": 6, "icon": "car-sport"},
    {"name": "Veloce GT Sport", "category": "veiculo", "subcategory": "Esportivos", "price": 120000, "description": "Iconic sports car", "appreciation": 0.02, "status_boost": 80, "level_required": 10, "icon": "car-sport"},
    {"name": "Presto Supercar", "category": "veiculo", "subcategory": "Esportivos", "price": 450000, "description": "Italian-style supercar", "appreciation": 0.05, "status_boost": 150, "level_required": 15, "icon": "car-sport"},
    {"name": "Coastal 32ft Yacht", "category": "veiculo", "subcategory": "Náuticos", "price": 95000, "description": "Yacht for coastal cruises", "appreciation": -0.03, "status_boost": 60, "level_required": 8, "icon": "boat"},
    {"name": "Grand Luxury Yacht", "category": "veiculo", "subcategory": "Náuticos", "price": 800000, "description": "Luxury yacht with 3 cabins and jacuzzi", "appreciation": 0.01, "status_boost": 200, "level_required": 18, "icon": "boat"},
    {"name": "SkyBird Helicopter", "category": "veiculo", "subcategory": "Aéreos", "price": 400000, "description": "Helicopter for urban transport", "appreciation": -0.02, "status_boost": 120, "level_required": 12, "icon": "airplane"},
    {"name": "AeroJet Executive 300", "category": "veiculo", "subcategory": "Aéreos", "price": 4000000, "description": "Private jet for international travel", "appreciation": 0.01, "status_boost": 500, "level_required": 20, "icon": "airplane"},
    # Real Estate
    {"name": "Studio Downtown", "category": "imovel", "subcategory": "Apartments", "price": 18000, "description": "25sqm studio in the city center", "appreciation": 0.03, "status_boost": 15, "level_required": 1, "icon": "home"},
    {"name": "2-Bed Apartment", "category": "imovel", "subcategory": "Apartments", "price": 55000, "description": "65sqm apartment in residential area", "appreciation": 0.04, "status_boost": 30, "level_required": 3, "icon": "home"},
    {"name": "3-Bed Family House", "category": "imovel", "subcategory": "Houses", "price": 95000, "description": "House with garden in gated community", "appreciation": 0.05, "status_boost": 50, "level_required": 5, "icon": "home"},
    {"name": "Duplex Penthouse", "category": "imovel", "subcategory": "Apartments", "price": 250000, "description": "180sqm penthouse with terrace and pool", "appreciation": 0.06, "status_boost": 100, "level_required": 8, "icon": "home"},
    {"name": "Hilltop Mansion", "category": "imovel", "subcategory": "Houses", "price": 900000, "description": "500sqm mansion with 6 suites and pool", "appreciation": 0.07, "status_boost": 250, "level_required": 15, "icon": "home"},
    {"name": "Skyline Penthouse", "category": "imovel", "subcategory": "Apartments", "price": 2000000, "description": "400sqm penthouse in the financial district", "appreciation": 0.08, "status_boost": 400, "level_required": 20, "icon": "home"},
    {"name": "Private Island", "category": "imovel", "subcategory": "Special", "price": 8000000, "description": "Private island with full infrastructure", "appreciation": 0.10, "status_boost": 1000, "level_required": 25, "icon": "globe"},
    # Luxury
    {"name": "Classic Diver Watch", "category": "luxo", "subcategory": "Watches", "price": 15000, "description": "Iconic Swiss diving timepiece", "appreciation": 0.08, "status_boost": 20, "level_required": 5, "icon": "watch"},
    {"name": "Grand Complication Watch", "category": "luxo", "subcategory": "Watches", "price": 90000, "description": "Ultra-luxury Swiss collector's piece", "appreciation": 0.12, "status_boost": 80, "level_required": 12, "icon": "watch"},
    {"name": "Prestige Handbag", "category": "luxo", "subcategory": "Accessories", "price": 25000, "description": "World's most desired luxury handbag", "appreciation": 0.15, "status_boost": 35, "level_required": 8, "icon": "bag"},
    {"name": "Fine Art Collection", "category": "luxo", "subcategory": "Art", "price": 350000, "description": "Collection of paintings from renowned artists", "appreciation": 0.10, "status_boost": 150, "level_required": 15, "icon": "color-palette"},
    {"name": "5-Carat Diamond", "category": "luxo", "subcategory": "Jewelry", "price": 150000, "description": "GIA-certified cut diamond", "appreciation": 0.06, "status_boost": 100, "level_required": 10, "icon": "diamond"},
]

async def seed_assets_for_sale():
    # Always reseed to update names/prices
    await db.assets_store.delete_many({})
    assets = []
    for seed in ASSETS_FOR_SALE:
        asset = {"id": str(uuid.uuid4()), **seed, "created_at": datetime.utcnow()}
        assets.append(asset)
    await db.assets_store.insert_many(assets)
    logger.info(f"Seeded {len(assets)} assets for sale")


async def startup_assets():
    await seed_assets_for_sale()

@router.get("/assets/store")
async def get_assets_store(category: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    query = {}
    if category:
        query['category'] = category
    assets = await db.assets_store.find(query).sort("price", 1).to_list(200)
    owned_ids = set()
    owned = await db.user_assets.find({"user_id": current_user['id']}).to_list(200)
    for o in owned:
        owned_ids.add(o.get('asset_store_id'))
    for a in assets:
        if '_id' in a:
            del a['_id']
        a['already_owned'] = a['id'] in owned_ids
    return assets

@router.post("/assets/buy")
async def buy_asset_item(request: dict, current_user: dict = Depends(get_current_user)):
    asset_id = request.get('asset_id')
    asset = await db.assets_store.find_one({"id": asset_id})
    if not asset:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    user = await db.users.find_one({"id": current_user['id']})
    if user['money'] < asset['price']:
        raise HTTPException(status_code=400, detail=f"Saldo insuficiente. Necessário: $ {asset['price']:,.2f}")
    if user.get('level', 1) < asset.get('level_required', 1):
        raise HTTPException(status_code=400, detail=f"Nível insuficiente. Requer nível {asset['level_required']}")
    already = await db.user_assets.find_one({"user_id": current_user['id'], "asset_store_id": asset_id})
    if already:
        raise HTTPException(status_code=400, detail="Você já possui este item")
    new_money = user['money'] - asset['price']
    await db.users.update_one({"id": current_user['id']}, {"$set": {"money": new_money}})
    user_asset = {
        "id": str(uuid.uuid4()),
        "user_id": current_user['id'],
        "asset_store_id": asset_id,
        "name": asset['name'],
        "category": asset['category'],
        "subcategory": asset['subcategory'],
        "icon": asset.get('icon', 'cube'),
        "purchase_price": asset['price'],
        "current_value": asset['price'],
        "appreciation": asset.get('appreciation', 0),
        "status_boost": asset.get('status_boost', 0),
        "description": asset['description'],
        "purchased_at": datetime.utcnow(),
    }
    await db.user_assets.insert_one(user_asset)
    return {
        "message": f"Parabéns! Você comprou {asset['name']}!",
        "item": asset['name'],
        "price": asset['price'],
        "status_boost": asset.get('status_boost', 0),
        "new_balance": round(new_money, 2),
    }

@router.get("/assets/owned")
async def get_owned_assets(current_user: dict = Depends(get_current_user)):
    assets = await db.user_assets.find({"user_id": current_user['id']}).to_list(200)
    total_value = 0
    total_invested = 0
    for a in assets:
        if '_id' in a:
            del a['_id']
        purchased_at = a.get('purchased_at', datetime.utcnow())
        if isinstance(purchased_at, str):
            purchased_at = datetime.fromisoformat(purchased_at.replace('Z', '+00:00'))
        months_owned = max(1, (datetime.utcnow() - purchased_at).days / 30)
        appreciation = a.get('appreciation', 0)
        a['current_value'] = round(a['purchase_price'] * (1 + appreciation * months_owned), 2)
        a['profit'] = round(a['current_value'] - a['purchase_price'], 2)
        a['profit_pct'] = round((a['profit'] / a['purchase_price']) * 100, 2) if a['purchase_price'] > 0 else 0
        total_value += a['current_value']
        total_invested += a['purchase_price']
        if a.get('purchased_at') and isinstance(a['purchased_at'], datetime):
            a['purchased_at'] = a['purchased_at'].isoformat()
    return {
        "assets": assets,
        "summary": {
            "total_value": round(total_value, 2),
            "total_invested": round(total_invested, 2),
            "total_profit": round(total_value - total_invested, 2),
            "count": len(assets),
            "total_status_boost": sum(a.get('status_boost', 0) for a in assets),
        }
    }

@router.post("/assets/sell")
async def sell_asset_item(request: dict, current_user: dict = Depends(get_current_user)):
    asset_id = request.get('asset_id')
    asset = await db.user_assets.find_one({"id": asset_id, "user_id": current_user['id']})
    if not asset:
        raise HTTPException(status_code=404, detail="Item não encontrado no seu patrimônio")
    purchased_at = asset.get('purchased_at', datetime.utcnow())
    if isinstance(purchased_at, str):
        purchased_at = datetime.fromisoformat(purchased_at.replace('Z', '+00:00'))
    months = max(1, (datetime.utcnow() - purchased_at).days / 30)
    sell_value = round(asset['purchase_price'] * (1 + asset.get('appreciation', 0) * months), 2)
    profit = sell_value - asset['purchase_price']
    user = await db.users.find_one({"id": current_user['id']})
    new_money = user['money'] + sell_value
    await db.users.update_one({"id": current_user['id']}, {"$set": {"money": new_money}})
    await db.user_assets.delete_one({"id": asset_id, "user_id": current_user['id']})
    return {
        "message": f"{asset['name']} vendido por $ {sell_value:,.2f}!",
        "sell_value": sell_value,
        "profit": round(profit, 2),
        "new_balance": round(new_money, 2),
    }



# ==================== ASSET IMAGES ====================

ASSET_IMAGES = {
    "moto_cg160": [
        "https://images.unsplash.com/photo-1558981806-ec527fa84c39?w=400&q=60",
        "https://images.unsplash.com/photo-1558980664-769d59546b3d?w=400&q=60",
        "https://images.unsplash.com/photo-1609630875171-b1321377ee65?w=400&q=60",
        "https://images.unsplash.com/photo-1568772585407-9361f9bf3a87?w=400&q=60",
    ],
    "fiat_uno": [
        "https://images.unsplash.com/photo-1502877338535-766e1452684a?w=400&q=60",
        "https://images.unsplash.com/photo-1494976388531-d1058494cdd8?w=400&q=60",
        "https://images.unsplash.com/photo-1503376780353-7e6692767b70?w=400&q=60",
        "https://images.unsplash.com/photo-1549399542-7e3f8b79c341?w=400&q=60",
    ],
    "civic_touring": [
        "https://images.unsplash.com/photo-1533473359331-0135ef1b58bf?w=400&q=60",
        "https://images.unsplash.com/photo-1552519507-da3b142c6e3d?w=400&q=60",
        "https://images.unsplash.com/photo-1542362567-b07e54358753?w=400&q=60",
        "https://images.unsplash.com/photo-1618843479313-40f8afb4b4d8?w=400&q=60",
    ],
    "bmw_x5": [
        "https://images.unsplash.com/photo-1555215695-3004980ad54e?w=400&q=60",
        "https://images.unsplash.com/photo-1556189250-72ba954cfc2b?w=400&q=60",
        "https://images.unsplash.com/photo-1617814076367-b759c7d7e738?w=400&q=60",
        "https://images.unsplash.com/photo-1580273916550-e323be2ae537?w=400&q=60",
    ],
    "kitnet": [
        "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=400&q=60",
        "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?w=400&q=60",
        "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=400&q=60",
        "https://images.unsplash.com/photo-1484154218962-a197022b5858?w=400&q=60",
    ],
    "apartamento": [
        "https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?w=400&q=60",
        "https://images.unsplash.com/photo-1560185893-a55cbc8c57e8?w=400&q=60",
        "https://images.unsplash.com/photo-1493809842364-78817add7ffb?w=400&q=60",
        "https://images.unsplash.com/photo-1512918728675-ed5a9ecdebfd?w=400&q=60",
    ],
    "casa_condominio": [
        "https://images.unsplash.com/photo-1613490493576-7fde63acd811?w=400&q=60",
        "https://images.unsplash.com/photo-1564013799919-ab600027ffc6?w=400&q=60",
        "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=400&q=60",
        "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=400&q=60",
    ],
    "mansao": [
        "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?w=400&q=60",
        "https://images.unsplash.com/photo-1613977257363-707ba9348227?w=400&q=60",
        "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=400&q=60",
        "https://images.unsplash.com/photo-1600566753190-17f0baa2a6c3?w=400&q=60",
    ],
    "rolex": [
        "https://images.unsplash.com/photo-1587836374828-4dbafa94cf0e?w=400&q=60",
        "https://images.unsplash.com/photo-1523170335258-f5ed11844a49?w=400&q=60",
        "https://images.unsplash.com/photo-1548171916-c8d1c1e8982c?w=400&q=60",
        "https://images.unsplash.com/photo-1522312346375-d1a52e2b99b3?w=400&q=60",
    ],
    "iate": [
        "https://images.unsplash.com/photo-1567899378494-47b22a2ae96a?w=400&q=60",
        "https://images.unsplash.com/photo-1544551763-46a013bb70d5?w=400&q=60",
        "https://images.unsplash.com/photo-1569263979104-865ab7cd8d13?w=400&q=60",
        "https://images.unsplash.com/photo-1605281317010-fe5ffe798166?w=400&q=60",
    ],
    "default_vehicle": [
        "https://images.unsplash.com/photo-1492144534655-ae79c964c9d7?w=400&q=60",
        "https://images.unsplash.com/photo-1583121274602-3e2820c69888?w=400&q=60",
        "https://images.unsplash.com/photo-1514316454349-750a7fd3da3a?w=400&q=60",
        "https://images.unsplash.com/photo-1485291571150-772bcfc10da5?w=400&q=60",
    ],
    "default_property": [
        "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=400&q=60",
        "https://images.unsplash.com/photo-1570129477492-45c003edd2be?w=400&q=60",
        "https://images.unsplash.com/photo-1568605114967-8130f3a36994?w=400&q=60",
        "https://images.unsplash.com/photo-1449844908441-8829872d2607?w=400&q=60",
    ],
    "default_luxury": [
        "https://images.unsplash.com/photo-1600003014755-ba31aa59c4b6?w=400&q=60",
        "https://images.unsplash.com/photo-1610375461246-83df859d849d?w=400&q=60",
        "https://images.unsplash.com/photo-1583937443999-b71b09a43c72?w=400&q=60",
        "https://images.unsplash.com/photo-1491637639811-60e2756cc1c7?w=400&q=60",
    ],
}

@router.get("/assets/images/{asset_key}")
async def get_asset_images(asset_key: str):
    """Get images for an asset by key or name"""
    # Direct key match
    images = ASSET_IMAGES.get(asset_key)
    if images:
        return {"images": images}
    
    # Fuzzy name match
    key_lower = asset_key.lower()
    for img_key in ASSET_IMAGES:
        if img_key in key_lower or key_lower in img_key:
            return {"images": ASSET_IMAGES[img_key]}
    
    # Category-based defaults via keyword matching
    if any(w in key_lower for w in ['moto', 'bike', 'cg', 'yamaha', 'honda']):
        return {"images": ASSET_IMAGES.get("moto_cg160", [])}
    if any(w in key_lower for w in ['fiat', 'uno', 'gol', 'carro', 'popular']):
        return {"images": ASSET_IMAGES.get("fiat_uno", [])}
    if any(w in key_lower for w in ['civic', 'corolla', 'sedan']):
        return {"images": ASSET_IMAGES.get("civic_touring", [])}
    if any(w in key_lower for w in ['bmw', 'suv', 'audi', 'mercedes']):
        return {"images": ASSET_IMAGES.get("bmw_x5", [])}
    if any(w in key_lower for w in ['kitnet', 'kit', 'studio', 'quitinete']):
        return {"images": ASSET_IMAGES.get("kitnet", [])}
    if any(w in key_lower for w in ['apartamento', 'apart', 'apto']):
        return {"images": ASSET_IMAGES.get("apartamento", [])}
    if any(w in key_lower for w in ['casa', 'condominio', 'sobrado']):
        return {"images": ASSET_IMAGES.get("casa_condominio", [])}
    if any(w in key_lower for w in ['mansao', 'mansion', 'palacio']):
        return {"images": ASSET_IMAGES.get("mansao", [])}
    if any(w in key_lower for w in ['rolex', 'relogio', 'watch']):
        return {"images": ASSET_IMAGES.get("rolex", [])}
    if any(w in key_lower for w in ['iate', 'yacht', 'barco', 'lancha']):
        return {"images": ASSET_IMAGES.get("iate", [])}
    if any(w in key_lower for w in ['ferrari', 'lamborghini', 'porsche', 'esportivo']):
        return {"images": ASSET_IMAGES.get("default_vehicle", [])}
    
    # Last resort: category fallback
    if any(w in key_lower for w in ['veiculo', 'carro', 'moto']):
        return {"images": ASSET_IMAGES.get("default_vehicle", [])}
    if any(w in key_lower for w in ['imovel', 'casa', 'apart', 'terreno']):
        return {"images": ASSET_IMAGES.get("default_property", [])}
    
    return {"images": ASSET_IMAGES.get("default_luxury", [])}



# ==================== ASSET OFFERS ====================

ASSET_OFFER_REASONS = [
    {"reason": "Colecionador interessado no imóvel", "emoji": "🏠", "multiplier_range": (1.10, 1.60), "type": "high"},
    {"reason": "Construtora quer o terreno", "emoji": "🏗️", "multiplier_range": (1.15, 1.45), "type": "high"},
    {"reason": "Investidor imobiliário estrangeiro", "emoji": "🌍", "multiplier_range": (1.08, 1.35), "type": "high"},
    {"reason": "Mercado imobiliário aquecido", "emoji": "📈", "multiplier_range": (1.05, 1.30), "type": "high"},
    {"reason": "Oferta de mercado padrão", "emoji": "📋", "multiplier_range": (0.90, 1.15), "type": "neutral"},
    {"reason": "Comprador aproveitando oportunidade", "emoji": "🦅", "multiplier_range": (0.80, 1.05), "type": "neutral"},
    {"reason": "Crise imobiliária - preço reduzido", "emoji": "📉", "multiplier_range": (0.65, 0.90), "type": "low"},
    {"reason": "Venda urgente por necessidade do comprador", "emoji": "⚠️", "multiplier_range": (0.70, 0.85), "type": "low"},
]

@router.get("/assets/offers")
async def get_asset_offers(current_user: dict = Depends(get_current_user)):
    """Get active purchase offers for user's assets. Generates new ones if needed."""
    user_id = current_user['id']
    now = datetime.utcnow()

    # Clean expired offers
    await db.asset_offers.delete_many({"user_id": user_id, "expires_at": {"$lt": now}})

    # Get active pending offers
    active_offers = await db.asset_offers.find({
        "user_id": user_id, "status": "pending", "expires_at": {"$gt": now}
    }).to_list(50)

    # Get user's assets
    user_assets = await db.user_assets.find({"user_id": user_id}).to_list(500)
    if not user_assets:
        return {"offers": [], "message": "Você não possui bens ou imóveis"}

    # Check cooldown
    assets_with_recent = set()
    recent = await db.asset_offers.find({
        "user_id": user_id, "created_at": {"$gt": now - timedelta(hours=3)}
    }).to_list(500)
    for o in recent:
        assets_with_recent.add(o.get('asset_id'))

    # Generate new offers (25% chance per asset)
    new_offers = []
    for asset in user_assets:
        if asset.get('id', str(asset.get('_id'))) in assets_with_recent:
            continue
        if _random.random() > 0.30:
            continue

        reason_data = _random.choice(ASSET_OFFER_REASONS)
        low, high = reason_data['multiplier_range']
        multiplier = round(_random.uniform(low, high), 2)
        purchase_price = asset.get('purchase_price', asset.get('price', 10000))
        offer_amount = round(purchase_price * multiplier)

        hours_to_expire = _random.randint(4, 24)
        asset_id = asset.get('id', str(asset.get('_id')))

        offer = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "asset_id": asset_id,
            "asset_name": asset.get('name', 'Bem'),
            "asset_category": asset.get('category', ''),
            "buyer_name": _generate_buyer_name(),
            "offer_amount": offer_amount,
            "purchase_price": purchase_price,
            "multiplier": multiplier,
            "reason": reason_data['reason'],
            "reason_emoji": reason_data['emoji'],
            "reason_type": reason_data['type'],
            "status": "pending",
            "created_at": now,
            "expires_at": now + timedelta(hours=hours_to_expire),
        }
        await db.asset_offers.insert_one(offer)
        new_offers.append(offer)

    all_active = active_offers + new_offers
    result = []
    for o in all_active:
        o.pop('_id', None)
        o['created_at'] = o['created_at'].isoformat() if isinstance(o.get('created_at'), datetime) else str(o.get('created_at', ''))
        o['expires_at'] = o['expires_at'].isoformat() if isinstance(o.get('expires_at'), datetime) else str(o.get('expires_at', ''))
        try:
            exp = datetime.fromisoformat(o['expires_at']) if isinstance(o['expires_at'], str) else o['expires_at']
            o['remaining_minutes'] = max(0, int((exp - now).total_seconds() / 60))
        except Exception:
            o['remaining_minutes'] = 0
        result.append(o)

    result.sort(key=lambda x: x.get('offer_amount', 0), reverse=True)
    return {"offers": result, "total_offers": len(result)}


@router.post("/assets/offers/respond")
async def respond_to_asset_offer(request: dict, current_user: dict = Depends(get_current_user)):
    """Accept or decline a purchase offer for an asset."""
    offer_id = request.get('offer_id')
    action = request.get('action')

    if action not in ('accept', 'decline'):
        raise HTTPException(status_code=400, detail="Ação inválida. Use 'accept' ou 'decline'")

    offer = await db.asset_offers.find_one({
        "id": offer_id, "user_id": current_user['id'], "status": "pending"
    })
    if not offer:
        raise HTTPException(status_code=404, detail="Oferta não encontrada ou já expirada")

    if datetime.utcnow() > offer.get('expires_at', datetime.utcnow()):
        await db.asset_offers.update_one({"id": offer_id}, {"$set": {"status": "expired"}})
        raise HTTPException(status_code=400, detail="Oferta expirada!")

    if action == 'decline':
        await db.asset_offers.update_one({"id": offer_id}, {"$set": {"status": "declined"}})
        return {"success": True, "message": f"Oferta de {offer.get('buyer_name')} recusada."}

    # Accept: sell asset
    asset = await db.user_assets.find_one({
        "id": offer['asset_id'], "user_id": current_user['id']
    })
    if not asset:
        asset = await db.user_assets.find_one({
            "_id": ObjectId(offer['asset_id']) if ObjectId.is_valid(offer['asset_id']) else None,
            "user_id": current_user['id']
        })
    if not asset:
        await db.asset_offers.update_one({"id": offer_id}, {"$set": {"status": "expired"}})
        raise HTTPException(status_code=404, detail="Bem não encontrado")

    offer_amount = offer.get('offer_amount', 0)
    await db.user_assets.delete_one({"_id": asset['_id']})

    user = await db.users.find_one({"id": current_user['id']})
    new_money = user['money'] + offer_amount
    xp_bonus = round(offer_amount * 0.01)
    new_xp = user.get('experience_points', 0) + xp_bonus

    await db.users.update_one({"id": current_user['id']}, {
        "$set": {"money": new_money, "experience_points": new_xp}
    })

    await db.asset_offers.update_one({"id": offer_id}, {"$set": {
        "status": "accepted", "accepted_at": datetime.utcnow()
    }})

    purchase_price = offer.get('purchase_price', 0)
    profit = offer_amount - purchase_price
    profit_text = f"Lucro: $ {profit:,.0f}" if profit >= 0 else f"Prejuízo: $ {abs(profit):,.0f}"

    return {
        "success": True,
        "message": f"'{asset.get('name')}' vendido para {offer.get('buyer_name')} por $ {offer_amount:,.0f}!\n\n{profit_text}\nXP Bônus: +{xp_bonus:,}",
        "offer_amount": offer_amount,
        "profit": profit,
        "xp_bonus": xp_bonus,
        "new_balance": round(new_money, 2),
    }



