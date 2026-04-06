"""BizRealms - Companies Routes."""
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional
from datetime import datetime, timedelta
from bson import ObjectId
import uuid
import random as _random
import math
import logging

logger = logging.getLogger(__name__)

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

# ==================== MAP / COMPANIES SYSTEM ====================

MAP_COMPANY_SEEDS = [
    # São Paulo - Centro
    {"name": "TechNova Solutions", "category": "tecnologia", "lat": -23.5505, "lng": -46.6333, "description": "Startup de IA e Machine Learning", "employees": 120, "revenue": "$ 15M/ano", "rating": 4.5, "city": "São Paulo"},
    {"name": "Banco Digital Plus", "category": "financeiro", "lat": -23.5475, "lng": -46.6361, "description": "Fintech de pagamentos digitais", "employees": 450, "revenue": "$ 200M/ano", "rating": 4.2, "city": "São Paulo"},
    {"name": "Café Paulistano", "category": "alimentacao", "lat": -23.5565, "lng": -46.6297, "description": "Rede de cafeterias premium", "employees": 85, "revenue": "$ 8M/ano", "rating": 4.7, "city": "São Paulo"},
    {"name": "Construtora Horizonte", "category": "construcao", "lat": -23.5615, "lng": -46.6555, "description": "Construtora de edifícios residenciais", "employees": 800, "revenue": "$ 500M/ano", "rating": 3.9, "city": "São Paulo"},
    # São Paulo - Faria Lima
    {"name": "Venture Capital BR", "category": "financeiro", "lat": -23.5735, "lng": -46.6895, "description": "Fundo de investimento em startups", "employees": 35, "revenue": "$ 2B AUM", "rating": 4.8, "city": "São Paulo"},
    {"name": "E-Commerce Master", "category": "varejo", "lat": -23.5750, "lng": -46.6850, "description": "Marketplace líder em eletrônicos", "employees": 2000, "revenue": "$ 1.2B/ano", "rating": 4.0, "city": "São Paulo"},
    {"name": "GreenEnergy Ltda", "category": "energia", "lat": -23.5685, "lng": -46.6920, "description": "Energia solar e sustentável", "employees": 200, "revenue": "$ 45M/ano", "rating": 4.3, "city": "São Paulo"},
    # São Paulo - Vila Olímpia
    {"name": "AppFactory Studio", "category": "tecnologia", "lat": -23.5950, "lng": -46.6800, "description": "Desenvolvimento de aplicativos mobile", "employees": 60, "revenue": "$ 12M/ano", "rating": 4.6, "city": "São Paulo"},
    {"name": "FitLife Academias", "category": "saude", "lat": -23.5920, "lng": -46.6755, "description": "Rede de academias premium", "employees": 350, "revenue": "$ 30M/ano", "rating": 4.1, "city": "São Paulo"},
    # São Paulo - Pinheiros
    {"name": "Agência Criativa 360", "category": "marketing", "lat": -23.5620, "lng": -46.6910, "description": "Marketing digital e branding", "employees": 40, "revenue": "$ 6M/ano", "rating": 4.4, "city": "São Paulo"},
    {"name": "Restaurante Sabores", "category": "alimentacao", "lat": -23.5630, "lng": -46.6935, "description": "Gastronomia contemporânea brasileira", "employees": 25, "revenue": "$ 3M/ano", "rating": 4.9, "city": "São Paulo"},
    # Rio de Janeiro
    {"name": "Petro Energy RJ", "category": "energia", "lat": -22.9068, "lng": -43.1729, "description": "Exploração de petróleo offshore", "employees": 5000, "revenue": "$ 10B/ano", "rating": 3.8, "city": "Rio de Janeiro"},
    {"name": "TurismoRio Ltda", "category": "turismo", "lat": -22.9519, "lng": -43.2105, "description": "Turismo e hotelaria", "employees": 150, "revenue": "$ 20M/ano", "rating": 4.0, "city": "Rio de Janeiro"},
    {"name": "GameStudio Carioca", "category": "tecnologia", "lat": -22.9137, "lng": -43.1764, "description": "Estúdio de jogos indie", "employees": 30, "revenue": "$ 4M/ano", "rating": 4.7, "city": "Rio de Janeiro"},
    # Belo Horizonte
    {"name": "MineralTech", "category": "mineracao", "lat": -19.9167, "lng": -43.9345, "description": "Tecnologia para mineração sustentável", "employees": 280, "revenue": "$ 80M/ano", "rating": 4.1, "city": "Belo Horizonte"},
    {"name": "Padaria Mineira Real", "category": "alimentacao", "lat": -19.9200, "lng": -43.9380, "description": "Padaria artesanal mineira", "employees": 15, "revenue": "$ 1.5M/ano", "rating": 4.8, "city": "Belo Horizonte"},
    # Curitiba
    {"name": "LogiTech Transportes", "category": "logistica", "lat": -25.4284, "lng": -49.2733, "description": "Logística e transporte rodoviário", "employees": 600, "revenue": "$ 150M/ano", "rating": 3.7, "city": "Curitiba"},
    {"name": "BioFarm Labs", "category": "saude", "lat": -25.4320, "lng": -49.2700, "description": "Pesquisa farmacêutica e biotecnologia", "employees": 90, "revenue": "$ 25M/ano", "rating": 4.5, "city": "Curitiba"},
    # Porto Alegre
    {"name": "AgroSul Grãos", "category": "agronegocio", "lat": -30.0346, "lng": -51.2177, "description": "Produção e exportação de grãos", "employees": 400, "revenue": "$ 300M/ano", "rating": 4.0, "city": "Porto Alegre"},
    {"name": "DesignGaúcho Studio", "category": "marketing", "lat": -30.0300, "lng": -51.2200, "description": "Design e UX para produtos digitais", "employees": 20, "revenue": "$ 2M/ano", "rating": 4.6, "city": "Porto Alegre"},
]

CATEGORY_INFO = {
    "tecnologia": {"icon": "laptop", "color": "#2196F3"},
    "financeiro": {"icon": "cash", "color": "#4CAF50"},
    "alimentacao": {"icon": "restaurant", "color": "#FF9800"},
    "construcao": {"icon": "construct", "color": "#795548"},
    "varejo": {"icon": "cart", "color": "#9C27B0"},
    "energia": {"icon": "flash", "color": "#FFC107"},
    "saude": {"icon": "medkit", "color": "#F44336"},
    "marketing": {"icon": "megaphone", "color": "#E91E63"},
    "turismo": {"icon": "airplane", "color": "#00BCD4"},
    "mineracao": {"icon": "hammer", "color": "#607D8B"},
    "logistica": {"icon": "bus", "color": "#3F51B5"},
    "agronegocio": {"icon": "leaf", "color": "#8BC34A"},
}

async def seed_map_companies():
    count = await db.map_companies.count_documents({})
    if count == 0:
        companies = []
        for seed in MAP_COMPANY_SEEDS:
            cat_info = CATEGORY_INFO.get(seed['category'], {"icon": "business", "color": "#888"})
            company = {
                "id": str(uuid.uuid4()),
                **seed,
                "icon": cat_info['icon'],
                "color": cat_info['color'],
                "open_positions": _random.randint(0, 5),
                "investment_available": _random.choice([True, False]),
                "min_investment": _random.choice([5000, 10000, 25000, 50000, 100000]),
                "created_at": datetime.utcnow(),
            }
            companies.append(company)
        await db.map_companies.insert_many(companies)
        logger.info(f"Seeded {len(companies)} map companies")


async def startup_map():
    await seed_map_companies()

@router.get("/map/companies")
async def get_map_companies(category: Optional[str] = None, city: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    """Get all companies for the map"""
    query = {}
    if category:
        query['category'] = category
    if city:
        query['city'] = city
    
    companies = await db.map_companies.find(query).to_list(200)
    for c in companies:
        if '_id' in c:
            del c['_id']
    
    return {"companies": companies, "categories": CATEGORY_INFO}

@router.get("/map/companies/{company_id}")
async def get_company_detail(company_id: str, current_user: dict = Depends(get_current_user)):
    """Get detailed company info"""
    company = await db.map_companies.find_one({"id": company_id})
    if not company:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    if '_id' in company:
        del company['_id']
    return company

# ==================== COMPANIES / ENTREPRENEURSHIP SYSTEM ====================

COMPANY_SEGMENTS = {
    "restaurante": {"icon": "restaurant", "color": "#FF5722", "label": "Restaurante"},
    "loja": {"icon": "storefront", "color": "#9C27B0", "label": "Loja/Varejo"},
    "tecnologia": {"icon": "hardware-chip", "color": "#2196F3", "label": "Tecnologia"},
    "fabrica": {"icon": "cog", "color": "#607D8B", "label": "Fábrica"},
    "saude": {"icon": "fitness", "color": "#F44336", "label": "Saúde"},
    "educacao": {"icon": "school", "color": "#FF9800", "label": "Educação"},
    "entretenimento": {"icon": "game-controller", "color": "#E91E63", "label": "Entretenimento"},
    "imobiliaria": {"icon": "home", "color": "#795548", "label": "Imobiliária"},
    "logistica": {"icon": "bus", "color": "#3F51B5", "label": "Logística"},
    "agronegocio": {"icon": "leaf", "color": "#4CAF50", "label": "Agronegócio"},
}

COMPANIES_FOR_SALE = [
    # Restaurantes
    {"name": "Lanchonete do Zé", "segment": "restaurante", "price": 15000, "daily_revenue": 100, "employees": 5, "description": "Lanchonete de bairro com clientela fiel", "level_required": 1},
    {"name": "Pizzaria Bella Napoli", "segment": "restaurante", "price": 80000, "daily_revenue": 400, "employees": 15, "description": "Pizzaria italiana com forno a lenha", "level_required": 3},
    {"name": "Rede Burger Premium", "segment": "restaurante", "price": 500000, "daily_revenue": 2167, "employees": 80, "description": "Rede de hamburguerias com 5 unidades", "level_required": 8},
    # Lojas
    {"name": "Bazar Popular", "segment": "loja", "price": 10000, "daily_revenue": 67, "employees": 3, "description": "Loja de variedades no centro", "level_required": 1},
    {"name": "Boutique Fashion", "segment": "loja", "price": 120000, "daily_revenue": 600, "employees": 8, "description": "Loja de roupas de grife", "level_required": 4},
    {"name": "Mega Store Eletrônicos", "segment": "loja", "price": 800000, "daily_revenue": 3000, "employees": 50, "description": "Loja de eletrônicos e tecnologia", "level_required": 10},
    # Tecnologia
    {"name": "Dev Studio Indie", "segment": "tecnologia", "price": 50000, "daily_revenue": 267, "employees": 4, "description": "Estúdio de desenvolvimento de apps", "level_required": 2},
    {"name": "SaaS Analytics Pro", "segment": "tecnologia", "price": 300000, "daily_revenue": 1500, "employees": 20, "description": "Plataforma SaaS de analytics", "level_required": 6},
    {"name": "CyberTech Security", "segment": "tecnologia", "price": 1500000, "daily_revenue": 6000, "employees": 100, "description": "Empresa de cibersegurança corporativa", "level_required": 12},
    # Fábricas
    {"name": "Confecção Básica", "segment": "fabrica", "price": 60000, "daily_revenue": 333, "employees": 20, "description": "Fábrica de camisetas e uniformes", "level_required": 3},
    {"name": "Fábrica de Móveis Artesanais", "segment": "fabrica", "price": 250000, "daily_revenue": 1167, "employees": 40, "description": "Produção de móveis sob medida", "level_required": 5},
    {"name": "Indústria Metalúrgica", "segment": "fabrica", "price": 2000000, "daily_revenue": 8333, "employees": 200, "description": "Produção de peças industriais", "level_required": 15},
    # Saúde
    {"name": "Farmácia Comunitária", "segment": "saude", "price": 40000, "daily_revenue": 233, "employees": 6, "description": "Farmácia de bairro com manipulação", "level_required": 2},
    {"name": "Clínica Odontológica", "segment": "saude", "price": 200000, "daily_revenue": 1000, "employees": 12, "description": "Clínica odontológica especializada", "level_required": 5},
    # Educação
    {"name": "Escola de Idiomas", "segment": "educacao", "price": 35000, "daily_revenue": 200, "employees": 8, "description": "Escola de inglês e espanhol", "level_required": 2},
    {"name": "Faculdade TechEdu", "segment": "educacao", "price": 1000000, "daily_revenue": 4000, "employees": 60, "description": "Faculdade de tecnologia EAD", "level_required": 10},
    # Entretenimento
    {"name": "Lan House Gamer", "segment": "entretenimento", "price": 25000, "daily_revenue": 150, "employees": 3, "description": "Espaço gamer com PCs de alta performance", "level_required": 1},
    {"name": "Parque Aquático Splash", "segment": "entretenimento", "price": 3000000, "daily_revenue": 11667, "employees": 150, "description": "Parque aquático com atrações radicais", "level_required": 15},
    # Imobiliária
    {"name": "Imobiliária Local", "segment": "imobiliaria", "price": 70000, "daily_revenue": 367, "employees": 5, "description": "Imobiliária focada em aluguéis", "level_required": 3},
    {"name": "Construtora Horizonte", "segment": "imobiliaria", "price": 5000000, "daily_revenue": 16667, "employees": 300, "description": "Construtora de prédios residenciais", "level_required": 18},
    # Logística
    {"name": "Motoboy Express", "segment": "logistica", "price": 20000, "daily_revenue": 117, "employees": 10, "description": "Serviço de entregas rápidas", "level_required": 1},
    {"name": "TransBR Cargas", "segment": "logistica", "price": 600000, "daily_revenue": 2500, "employees": 45, "description": "Transportadora rodoviária nacional", "level_required": 8},
    # Agronegócio
    {"name": "Horta Orgânica", "segment": "agronegocio", "price": 18000, "daily_revenue": 107, "employees": 4, "description": "Produção de hortaliças orgânicas", "level_required": 1},
    {"name": "Fazenda Boi Gordo", "segment": "agronegocio", "price": 2500000, "daily_revenue": 9333, "employees": 50, "description": "Fazenda de gado de corte premium", "level_required": 12},
]

class CreateCompanyRequest(BaseModel):
    name: str
    segment: str

class MergeCompaniesRequest(BaseModel):
    company_id_1: str
    company_id_2: str

async def seed_companies_for_sale():
    count = await db.companies_for_sale.count_documents({})
    if count == 0:
        companies = []
        for seed in COMPANIES_FOR_SALE:
            seg = COMPANY_SEGMENTS.get(seed['segment'], {})
            company = {
                "id": str(uuid.uuid4()),
                **seed,
                "icon": seg.get('icon', 'business'),
                "color": seg.get('color', '#888'),
                "created_at": datetime.utcnow(),
            }
            companies.append(company)
        await db.companies_for_sale.insert_many(companies)
        logger.info(f"Seeded {len(companies)} companies for sale")


async def startup_companies():
    await seed_companies_for_sale()

@router.get("/companies/segments")
async def get_segments(current_user: dict = Depends(get_current_user)):
    return COMPANY_SEGMENTS

@router.get("/companies/available")
async def get_companies_available(segment: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    query = {}
    if segment:
        query['segment'] = segment
    companies = await db.companies_for_sale.find(query).sort("price", 1).to_list(200)
    owned_ids = set()
    owned = await db.user_companies.find({"user_id": current_user['id']}).to_list(200)
    for o in owned:
        if o.get('source_company_id'):
            owned_ids.add(o['source_company_id'])
    result = []
    for c in companies:
        if '_id' in c:
            del c['_id']
        c['already_owned'] = c['id'] in owned_ids
        result.append(c)
    return result

@router.post("/companies/buy")
async def buy_company(request: dict, current_user: dict = Depends(get_current_user)):
    company_id = request.get('company_id')
    company = await db.companies_for_sale.find_one({"id": company_id})
    if not company:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    user = await db.users.find_one({"id": current_user['id']})
    if user['money'] < company['price']:
        raise HTTPException(status_code=400, detail=f"Saldo insuficiente. Necessário: $ {company['price']:,.2f}")
    if (user.get('level', 1)) < company.get('level_required', 1):
        raise HTTPException(status_code=400, detail=f"Nível insuficiente. Requer nível {company['level_required']}")
    already = await db.user_companies.find_one({"user_id": current_user['id'], "source_company_id": company_id})
    if already:
        raise HTTPException(status_code=400, detail="Você já possui esta empresa")
    new_money = user['money'] - company['price']
    await db.users.update_one({"id": current_user['id']}, {"$set": {"money": new_money}})
    user_company = {
        "id": str(uuid.uuid4()),
        "user_id": current_user['id'],
        "source_company_id": company_id,
        "name": company['name'],
        "segment": company['segment'],
        "icon": company.get('icon', 'business'),
        "color": company.get('color', '#888'),
        "daily_revenue": company['monthly_revenue'],
        "employees": company['employees'],
        "description": company['description'],
        "purchase_price": company['price'],
        "level": 1,
        "revenue_multiplier": 1.0,
        "total_collected": 0,
        "last_collection": datetime.utcnow(),
        "ad_boost_expires": None,
        "purchased_at": datetime.utcnow(),
    }
    await db.user_companies.insert_one(user_company)
    return {
        "message": f"Parabéns! Você comprou {company['name']}!",
        "company_name": company['name'],
        "price": company['price'],
        "daily_revenue": company['monthly_revenue'],
        "roi_months": round(company['price'] / company['monthly_revenue'], 1) if company['monthly_revenue'] > 0 else 0,
        "new_balance": round(new_money, 2),
    }

@router.post("/companies/create")
async def create_company(request: CreateCompanyRequest, current_user: dict = Depends(get_current_user)):
    if request.segment not in COMPANY_SEGMENTS:
        raise HTTPException(status_code=400, detail="Segmento inválido")
    user = await db.users.find_one({"id": current_user['id']})
    creation_cost = 5000
    if user['money'] < creation_cost:
        raise HTTPException(status_code=400, detail=f"Saldo insuficiente. Custo de criação: $ {creation_cost:,.2f}")
    new_money = user['money'] - creation_cost
    await db.users.update_one({"id": current_user['id']}, {"$set": {"money": new_money}})
    seg = COMPANY_SEGMENTS[request.segment]
    base_revenue = _random.randint(800, 2500)
    user_company = {
        "id": str(uuid.uuid4()),
        "user_id": current_user['id'],
        "source_company_id": None,
        "name": request.name,
        "segment": request.segment,
        "icon": seg['icon'],
        "color": seg['color'],
        "daily_revenue": base_revenue,
        "employees": _random.randint(1, 5),
        "description": f"Empresa criada pelo jogador no segmento {seg['label']}",
        "purchase_price": creation_cost,
        "level": 1,
        "revenue_multiplier": 1.0,
        "total_collected": 0,
        "last_collection": datetime.utcnow(),
        "ad_boost_expires": None,
        "is_custom": True,
        "purchased_at": datetime.utcnow(),
    }
    await db.user_companies.insert_one(user_company)
    return {
        "message": f"{request.name} criada com sucesso!",
        "company": {"name": request.name, "segment": request.segment, "daily_revenue": base_revenue},
        "new_balance": round(new_money, 2),
    }

@router.get("/companies/owned")
async def get_owned_companies(current_user: dict = Depends(get_current_user)):
    companies = await db.user_companies.find({"user_id": current_user['id']}).to_list(200)
    now = datetime.utcnow()
    total_monthly = 0
    for c in companies:
        if '_id' in c:
            del c['_id']
        boost_active = False
        if c.get('ad_boost_expires') and c['ad_boost_expires'] > now:
            boost_active = True
        c['ad_boost_active'] = boost_active
        effective_mult = c.get('revenue_multiplier', 1.0) * (2.0 if boost_active else 1.0)
        base_rev = c.get('daily_revenue', c.get('monthly_revenue', 0) / 30 if c.get('monthly_revenue') else 0)
        c['daily_revenue'] = base_rev
        c['effective_revenue'] = round(base_rev * effective_mult)
        c['effective_multiplier'] = effective_mult
        if c.get('ad_boost_expires'):
            c['ad_boost_remaining'] = max(0, int((c['ad_boost_expires'] - now).total_seconds()))
            c['ad_boost_expires'] = c['ad_boost_expires'].isoformat()
        else:
            c['ad_boost_remaining'] = 0
        if c.get('last_collection'):
            c['last_collection'] = c['last_collection'].isoformat()
        if c.get('purchased_at'):
            c['purchased_at'] = c['purchased_at'].isoformat()
        # ROI calculation
        purchase_price = c.get('purchase_price', 0)
        total_collected = c.get('total_collected', 0)
        daily_rev_val = c.get('daily_revenue', c.get('monthly_revenue', 1) / 30 if c.get('monthly_revenue') else 1)
        c['roi_months'] = round(purchase_price / (daily_rev_val * 30), 1) if daily_rev_val > 0 else 0
        c['roi_progress'] = round((total_collected / purchase_price) * 100, 1) if purchase_price > 0 else 0
        c['roi_recovered'] = total_collected >= purchase_price
        total_monthly += c['effective_revenue']
    return {"companies": companies, "total_daily_revenue": total_monthly, "count": len(companies)}

@router.post("/companies/collect-revenue")
async def collect_company_revenue(current_user: dict = Depends(get_current_user)):
    companies = await db.user_companies.find({"user_id": current_user['id']}).to_list(200)
    if not companies:
        raise HTTPException(status_code=400, detail="Você não possui empresas")
    now = datetime.utcnow()
    total_revenue = 0
    details = []
    # Game time: 30 game days = 24 real hours => 1 game day = 2880 real seconds
    GAME_DAY_SECONDS = 2880
    for c in companies:
        last = c.get('last_collection', now)
        if isinstance(last, str):
            last = datetime.fromisoformat(last.replace('Z', '+00:00'))
        game_days = (now - last).total_seconds() / GAME_DAY_SECONDS
        if game_days < 0.001:
            continue
        daily_rev = c.get('daily_revenue', c.get('monthly_revenue', 0) / 30 if c.get('monthly_revenue') else 0)
        boost_active = c.get('ad_boost_expires') and c['ad_boost_expires'] > now
        mult = c.get('revenue_multiplier', 1.0) * (2.0 if boost_active else 1.0)
        rev = daily_rev * game_days * mult
        total_revenue += rev
        await db.user_companies.update_one(
            {"id": c['id']},
            {"$set": {"last_collection": now}, "$inc": {"total_collected": rev}}
        )
        details.append({"name": c['name'], "revenue": round(rev, 2), "days": round(game_days, 2)})
    if total_revenue > 0:
        user = await db.users.find_one({"id": current_user['id']})
        new_money = user['money'] + total_revenue
        xp_gain = int(total_revenue / 10)
        new_xp = user.get('experience_points', 0) + xp_gain
        new_level = (new_xp // 1000) + 1
        await db.users.update_one(
            {"id": current_user['id']},
            {"$set": {"money": new_money, "experience_points": new_xp, "level": new_level}}
        )
        return {
            "message": f"Receitas coletadas: $ {total_revenue:,.2f}",
            "total_revenue": round(total_revenue, 2),
            "xp_gained": xp_gain,
            "details": details,
            "new_balance": round(new_money, 2),
        }
    return {"message": "Nenhuma receita para coletar ainda", "total_revenue": 0, "details": []}

@router.post("/companies/ad-boost")
async def company_ad_boost(current_user: dict = Depends(get_current_user)):
    companies = await db.user_companies.find({"user_id": current_user['id']}).to_list(200)
    if not companies:
        raise HTTPException(status_code=400, detail="Você não possui empresas")
    expires = datetime.utcnow() + timedelta(hours=6)
    for c in companies:
        await db.user_companies.update_one({"id": c['id']}, {"$set": {"ad_boost_expires": expires}})
    return {
        "message": "Boost ativado! Rendimentos de TODAS as empresas duplicados por 6 horas!",
        "boost_duration_hours": 6,
        "expires_at": expires.isoformat(),
        "companies_boosted": len(companies),
    }

@router.post("/companies/merge")
async def merge_companies(request: MergeCompaniesRequest, current_user: dict = Depends(get_current_user)):
    c1 = await db.user_companies.find_one({"id": request.company_id_1, "user_id": current_user['id']})
    c2 = await db.user_companies.find_one({"id": request.company_id_2, "user_id": current_user['id']})
    if not c1 or not c2:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    if c1['segment'] != c2['segment']:
        raise HTTPException(status_code=400, detail="Só é possível fundir empresas do mesmo segmento")
    merged_name = f"{c1['name']} & {c2['name']}"
    merged_revenue = int((c1['monthly_revenue'] + c2['monthly_revenue']) * 1.3)
    merged_employees = c1['employees'] + c2['employees']
    new_level = max(c1.get('level', 1), c2.get('level', 1)) + 1
    await db.user_companies.update_one(
        {"id": c1['id']},
        {"$set": {
            "name": merged_name,
            "daily_revenue": merged_revenue,
            "employees": merged_employees,
            "level": new_level,
            "revenue_multiplier": c1.get('revenue_multiplier', 1.0) + 0.2,
            "description": f"Resultado da fusão de {c1['name']} e {c2['name']}. Nível {new_level}.",
        }}
    )
    await db.user_companies.delete_one({"id": c2['id']})
    return {
        "message": f"Fusão concluída! {merged_name} criada com +30% de receita!",
        "new_company": {"name": merged_name, "daily_revenue": merged_revenue, "level": new_level},
    }



# ==================== EMPRESAS - SELL & FRANCHISE IMPROVEMENTS ====================

@router.post("/companies/sell")
async def sell_company(request: dict, current_user: dict = Depends(get_current_user)):
    """Sell an owned company"""
    company_id = request.get('company_id')
    
    company = await db.user_companies.find_one({"id": company_id, "user_id": current_user['id']})
    if not company:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    
    # Sell price: 80% of purchase price + collected revenue bonus
    sell_price = round(company.get('purchase_price', 0) * 0.8)
    
    # Calculate ROI info
    purchase_price = company.get('purchase_price', 0)
    total_collected = company.get('total_collected', 0)
    total_return = total_collected + sell_price
    profit = total_return - purchase_price
    roi_positive = profit >= 0
    
    # Also delete all franchises of this company
    if not company.get('is_franchise'):
        franchise_count = await db.user_companies.count_documents({"parent_company_id": company_id, "user_id": current_user['id']})
        if franchise_count > 0:
            await db.user_companies.delete_many({"parent_company_id": company_id, "user_id": current_user['id']})
    
    await db.user_companies.delete_one({"_id": company['_id']})
    
    user = await db.users.find_one({"id": current_user['id']})
    new_money = user['money'] + sell_price
    await db.users.update_one({"id": current_user['id']}, {"$set": {"money": new_money}})
    
    roi_text = f"Lucro: +$ {profit:,.0f}" if roi_positive else f"Prejuízo: -$ {abs(profit):,.0f}"
    
    return {
        "success": True,
        "message": f"Empresa '{company.get('name')}' vendida por $ {sell_price:,.0f}!",
        "sell_price": sell_price,
        "new_balance": round(new_money, 2),
        "roi": {
            "purchase_price": purchase_price,
            "total_collected": total_collected,
            "sell_price": sell_price,
            "total_return": total_return,
            "profit": profit,
            "roi_positive": roi_positive,
            "roi_text": roi_text,
        },
    }


# ==================== COMPANY PURCHASE OFFERS ====================


OFFER_REASONS = [
    {"reason": "Investidor estrangeiro interessado", "emoji": "🌍", "multiplier_range": (1.05, 1.50), "type": "high"},
    {"reason": "Fundo de investimento quer adquirir", "emoji": "🏦", "multiplier_range": (1.10, 1.40), "type": "high"},
    {"reason": "Concorrente quer eliminar competição", "emoji": "⚔️", "multiplier_range": (1.15, 1.35), "type": "high"},
    {"reason": "Mercado aquecido no setor", "emoji": "📈", "multiplier_range": (1.08, 1.30), "type": "high"},
    {"reason": "Empresa chamou atenção da mídia", "emoji": "📺", "multiplier_range": (1.02, 1.25), "type": "high"},
    {"reason": "Grupo empresarial em expansão", "emoji": "🏢", "multiplier_range": (1.00, 1.20), "type": "neutral"},
    {"reason": "Oferta padrão de mercado", "emoji": "📋", "multiplier_range": (0.90, 1.10), "type": "neutral"},
    {"reason": "Investidor oportunista", "emoji": "🦅", "multiplier_range": (0.85, 1.05), "type": "neutral"},
    {"reason": "Crise no setor - comprador a preço baixo", "emoji": "📉", "multiplier_range": (0.70, 0.90), "type": "low"},
    {"reason": "Liquidação forçada por dívidas do comprador", "emoji": "⚠️", "multiplier_range": (0.65, 0.85), "type": "low"},
    {"reason": "Startup querendo o ponto comercial", "emoji": "🚀", "multiplier_range": (0.75, 0.95), "type": "low"},
]

BUYER_FIRST_NAMES = ["Carlos", "Marina", "Roberto", "Ana", "Pedro", "Fernanda", "Lucas", "Juliana", "Rafael", "Camila",
                     "Gabriel", "Isabela", "Thiago", "Larissa", "Matheus", "Patrícia", "Bruno", "Vanessa", "Diego", "Renata"]
BUYER_LAST_NAMES = ["Silva", "Santos", "Oliveira", "Souza", "Rodrigues", "Ferreira", "Almeida", "Pereira", "Lima", "Gomes",
                    "Costa", "Ribeiro", "Martins", "Carvalho", "Araújo", "Melo", "Barbosa", "Cardoso", "Correia", "Dias"]
BUYER_COMPANIES = ["Capital Invest", "Grupo Alpha", "Nexus Holdings", "Venture BR", "Fênix Capital", "Athena Partners",
                   "Ômega Corp", "Summit Group", "Prisma Investimentos", "Atlas Holdings", "Titan Capital", "Nova Era Group"]


def _generate_buyer_name():
    if _random.random() < 0.5:
        return f"{_random.choice(BUYER_FIRST_NAMES)} {_random.choice(BUYER_LAST_NAMES)}"
    else:
        return _random.choice(BUYER_COMPANIES)


@router.get("/companies/offers")
async def get_company_offers(current_user: dict = Depends(get_current_user)):
    """Get active purchase offers for user's companies. Generates new ones if needed."""
    user_id = current_user['id']
    now = datetime.utcnow()

    # Clean expired offers
    await db.company_offers.delete_many({"user_id": user_id, "expires_at": {"$lt": now}})

    # Get active pending offers
    active_offers = await db.company_offers.find({
        "user_id": user_id,
        "status": "pending",
        "expires_at": {"$gt": now}
    }).to_list(50)

    # Get user's companies
    user_companies = await db.user_companies.find({"user_id": user_id}).to_list(500)
    if not user_companies:
        return {"offers": [], "message": "Você não possui empresas"}

    # Check cooldown: generate new offers at most every 2 hours per company
    companies_with_recent_offer = set()
    all_offers = await db.company_offers.find({
        "user_id": user_id,
        "created_at": {"$gt": now - timedelta(hours=2)}
    }).to_list(500)
    for o in all_offers:
        companies_with_recent_offer.add(o.get('company_id'))

    # Generate new offers for companies without recent ones (30% chance per company)
    new_offers = []
    for company in user_companies:
        cid = str(company.get('_id', company.get('id', '')))
        if cid in companies_with_recent_offer:
            continue
        if _random.random() > 0.35:
            continue

        reason_data = _random.choice(OFFER_REASONS)
        low, high = reason_data['multiplier_range']
        multiplier = round(_random.uniform(low, high), 2)
        purchase_price = company.get('purchase_price', 10000)
        offer_amount = round(purchase_price * multiplier)

        # Higher level companies get slightly better offers
        company_level = company.get('level', 1)
        if company_level > 3:
            offer_amount = round(offer_amount * (1 + (company_level - 3) * 0.02))

        # Expires in 4-24 hours
        hours_to_expire = _random.randint(4, 24)
        expires_at = now + timedelta(hours=hours_to_expire)

        offer = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "company_id": cid,
            "company_name": company.get('name', 'Empresa'),
            "company_segment": company.get('segment', ''),
            "buyer_name": _generate_buyer_name(),
            "offer_amount": offer_amount,
            "purchase_price": purchase_price,
            "multiplier": multiplier,
            "reason": reason_data['reason'],
            "reason_emoji": reason_data['emoji'],
            "reason_type": reason_data['type'],
            "status": "pending",
            "created_at": now,
            "expires_at": expires_at,
        }
        await db.company_offers.insert_one(offer)
        new_offers.append(offer)

    # Merge with active
    all_active = active_offers + new_offers
    # Remove _id for serialization
    result = []
    for o in all_active:
        o.pop('_id', None)
        o['created_at'] = o['created_at'].isoformat() if isinstance(o.get('created_at'), datetime) else str(o.get('created_at', ''))
        o['expires_at'] = o['expires_at'].isoformat() if isinstance(o.get('expires_at'), datetime) else str(o.get('expires_at', ''))
        # Calculate time remaining in minutes
        try:
            exp = datetime.fromisoformat(o['expires_at']) if isinstance(o['expires_at'], str) else o['expires_at']
            remaining_minutes = max(0, int((exp - now).total_seconds() / 60))
            o['remaining_minutes'] = remaining_minutes
        except Exception:
            o['remaining_minutes'] = 0
        result.append(o)

    # Sort by offer amount descending
    result.sort(key=lambda x: x.get('offer_amount', 0), reverse=True)

    return {"offers": result, "total_offers": len(result)}


@router.post("/companies/offers/respond")
async def respond_to_offer(request: dict, current_user: dict = Depends(get_current_user)):
    """Accept or decline a purchase offer"""
    offer_id = request.get('offer_id')
    action = request.get('action')  # 'accept' or 'decline'

    if action not in ('accept', 'decline'):
        raise HTTPException(status_code=400, detail="Ação inválida. Use 'accept' ou 'decline'")

    offer = await db.company_offers.find_one({
        "id": offer_id,
        "user_id": current_user['id'],
        "status": "pending"
    })
    if not offer:
        raise HTTPException(status_code=404, detail="Oferta não encontrada ou já expirada")

    # Check if offer is still valid
    if datetime.utcnow() > offer.get('expires_at', datetime.utcnow()):
        await db.company_offers.update_one({"id": offer_id}, {"$set": {"status": "expired"}})
        raise HTTPException(status_code=400, detail="Oferta expirada!")

    if action == 'decline':
        await db.company_offers.update_one({"id": offer_id}, {"$set": {"status": "declined"}})
        return {"success": True, "message": f"Oferta de {offer.get('buyer_name')} recusada."}

    # Accept: sell the company at the offer price
    company = await db.user_companies.find_one({
        "id": offer['company_id'],
        "user_id": current_user['id']
    })
    if not company:
        await db.company_offers.update_one({"id": offer_id}, {"$set": {"status": "expired"}})
        raise HTTPException(status_code=404, detail="Empresa não encontrada (pode já ter sido vendida)")

    offer_amount = offer.get('offer_amount', 0)

    # Delete franchises if parent company
    if not company.get('is_franchise'):
        await db.user_companies.delete_many({
            "parent_company_id": company['id'],
            "user_id": current_user['id']
        })

    # Delete the company
    await db.user_companies.delete_one({"_id": company['_id']})

    # Credit the player
    user = await db.users.find_one({"id": current_user['id']})
    new_money = user['money'] + offer_amount
    xp_bonus = round(offer_amount * 0.01)  # 1% of offer as XP
    new_xp = user.get('experience', 0) + xp_bonus

    await db.users.update_one({"id": current_user['id']}, {
        "$set": {"money": new_money, "experience": new_xp}
    })

    # Mark offer as accepted and invalidate other offers for same company
    await db.company_offers.update_one({"id": offer_id}, {"$set": {"status": "accepted"}})
    await db.company_offers.update_many(
        {"company_id": offer['company_id'], "user_id": current_user['id'], "status": "pending"},
        {"$set": {"status": "expired"}}
    )

    profit = offer_amount - offer.get('purchase_price', 0)
    profit_text = f"Lucro: $ {profit:,.0f}" if profit >= 0 else f"Prejuízo: $ {abs(profit):,.0f}"

    return {
        "success": True,
        "message": f"Empresa '{company.get('name')}' vendida para {offer.get('buyer_name')} por $ {offer_amount:,.0f}!\n\n{profit_text}\nXP Bônus: +{xp_bonus:,}",
        "offer_amount": offer_amount,
        "profit": profit,
        "xp_bonus": xp_bonus,
        "new_balance": round(new_money, 2),
    }


@router.post("/companies/offers/improve")
async def improve_offer_via_ad(request: dict, current_user: dict = Depends(get_current_user)):
    """Improve an offer amount after watching an ad (15-25% increase)"""
    offer_id = request.get('offer_id')
    if not offer_id:
        raise HTTPException(status_code=400, detail="offer_id required")

    offer = await db.company_offers.find_one({
        "id": offer_id,
        "user_id": current_user['id'],
        "status": "pending"
    })
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found or already expired")

    # Check if already improved
    if offer.get('ad_improved'):
        raise HTTPException(status_code=400, detail="This offer was already improved")

    # Calculate improvement (15-25%)
    improvement_factor = 1 + _random.uniform(0.15, 0.25)
    old_amount = offer.get('offer_amount', 0)
    if old_amount <= 0:
        # Fallback: recalculate from company purchase price
        company = await db.user_companies.find_one({"id": offer.get('company_id'), "user_id": current_user['id']})
        old_amount = int(company.get('purchase_price', 10000) * offer.get('multiplier', 1.0)) if company else 10000
    new_amount = int(round(old_amount * improvement_factor))

    await db.company_offers.update_one(
        {"id": offer_id},
        {"$set": {"offer_amount": new_amount, "ad_improved": True}}
    )

    company = await db.user_companies.find_one({"id": offer['company_id'], "user_id": current_user['id']})
    purchase_price = company.get('purchase_price', old_amount) if company else old_amount

    return {
        "success": True,
        "offer_id": offer_id,
        "old_amount": old_amount,
        "new_amount": new_amount,
        "multiplier": round(new_amount / purchase_price, 2) if purchase_price > 0 else 1.0,
        "improvement_pct": round((improvement_factor - 1) * 100, 1),
        "message": f"Offer improved by {round((improvement_factor - 1) * 100)}%! New value: $ {new_amount:,.0f}"
    }





# ==================== FRANCHISE SYSTEM (FRANQUIAS) ====================

FRANCHISE_SEGMENTS = ['restaurante', 'loja', 'fabrica']

@router.post("/companies/create-franchise")
async def create_franchise(request: dict, current_user: dict = Depends(get_current_user)):
    """Create a franchise from an existing company (retail/similar segments only)"""
    company_id = request.get('company_id')
    franchise_name = request.get('franchise_name', '')
    franchise_location = request.get('franchise_location', 'Nova Unidade')
    
    # Find the parent company
    parent = await db.user_companies.find_one({
        "id": company_id,
        "user_id": current_user['id']
    })
    if not parent:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    
    segment = parent.get('segment', '')
    if segment not in FRANCHISE_SEGMENTS:
        raise HTTPException(status_code=400, detail=f"Apenas empresas de varejo, restaurantes e fábricas podem criar franquias. Segmento '{segment}' não é elegível.")
    
    # Check user funds - franchise costs 60% of parent
    franchise_cost = parent.get('purchase_price', 0) * 0.6
    user = await db.users.find_one({"id": current_user['id']})
    if user['money'] < franchise_cost:
        raise HTTPException(status_code=400, detail=f"Saldo insuficiente. Custo da franquia: $ {franchise_cost:,.0f}")
    
    # Count existing franchises for this parent
    existing_franchises = await db.user_companies.count_documents({
        "user_id": current_user['id'],
        "parent_company_id": company_id
    })
    max_franchises = 250
    if existing_franchises >= max_franchises:
        raise HTTPException(status_code=400, detail=f"Limite de {max_franchises} franquias por empresa atingido")
    
    # Franchise earns 70% of parent revenue
    franchise_revenue = round(parent.get('monthly_revenue', 0) * 0.7)
    
    # Deduct money
    new_money = user['money'] - franchise_cost
    await db.users.update_one({"id": current_user['id']}, {"$set": {"money": new_money}})
    
    # Create franchise
    fname = franchise_name or f"{parent.get('name', 'Empresa')} - Franquia {existing_franchises + 1}"
    franchise = {
        "id": str(uuid.uuid4()),
        "user_id": current_user['id'],
        "name": fname,
        "segment": segment,
        "purchase_price": franchise_cost,
        "daily_revenue": franchise_revenue,
        "employees": max(1, parent.get('employees', 1) // 2),
        "description": f"Franquia de {parent.get('name', '')} - {franchise_location}",
        "is_franchise": True,
        "parent_company_id": company_id,
        "parent_company_name": parent.get('name', ''),
        "location": franchise_location,
        "icon": parent.get('icon', 'business'),
        "color": parent.get('color', '#4CAF50'),
        "created_at": datetime.utcnow(),
    }
    await db.user_companies.insert_one(franchise)
    
    return {
        "success": True,
        "message": f"Franquia '{fname}' criada com sucesso!",
        "franchise": {k: v for k, v in franchise.items() if k != '_id'},
        "cost": franchise_cost,
        "daily_revenue": franchise_revenue,
        "new_balance": round(new_money, 2),
    }



