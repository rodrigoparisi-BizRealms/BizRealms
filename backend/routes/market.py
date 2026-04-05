"""BizRealms - Market Routes."""
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

# ==================== DYNAMIC MARKET EVENTS ====================

MARKET_EVENTS = [
    {"id": "bull_run", "title": "Alta do Mercado!", "description": "Otimismo generalizado eleva os preços das ações", "icon": "trending-up", "color": "#4CAF50", "effect": {"acoes": 1.15, "crypto": 1.10}, "duration_hours": 6},
    {"id": "crypto_boom", "title": "Boom das Criptos!", "description": "Bitcoin atinge nova máxima histórica, arrastando todo o mercado", "icon": "rocket", "color": "#FF9800", "effect": {"crypto": 1.30}, "duration_hours": 4},
    {"id": "market_crash", "title": "Crash do Mercado!", "description": "Pânico nos mercados após crise bancária global", "icon": "trending-down", "color": "#F44336", "effect": {"acoes": 0.85, "crypto": 0.80, "fundos": 0.90}, "duration_hours": 8},
    {"id": "tech_rally", "title": "Rally da Tecnologia!", "description": "Resultados trimestrais surpreendem e setor tech dispara", "icon": "logo-apple", "color": "#2196F3", "effect": {"acoes": 1.12}, "duration_hours": 5},
    {"id": "gold_rush", "title": "Corrida do Ouro!", "description": "Incerteza política leva investidores a buscar refúgio em commodities", "icon": "diamond", "color": "#FFD700", "effect": {"commodities": 1.25}, "duration_hours": 6},
    {"id": "inflation_fear", "title": "Medo da Inflação!", "description": "Dados de inflação acima do esperado assustam investidores", "icon": "alert-circle", "color": "#FF5722", "effect": {"acoes": 0.92, "fundos": 0.88}, "duration_hours": 12},
    {"id": "regulation_news", "title": "Nova Regulação Cripto!", "description": "Governo anuncia regulação favorável para criptomoedas", "icon": "shield-checkmark", "color": "#9C27B0", "effect": {"crypto": 1.20}, "duration_hours": 8},
    {"id": "ipo_hype", "title": "Onda de IPOs!", "description": "Várias empresas abrem capital e mercado aquece", "icon": "business", "color": "#00BCD4", "effect": {"acoes": 1.10}, "duration_hours": 6},
    {"id": "economic_recovery", "title": "Recuperação Econômica!", "description": "PIB cresce acima do esperado e mercados celebram", "icon": "sunny", "color": "#4CAF50", "effect": {"acoes": 1.08, "fundos": 1.06, "commodities": 1.05}, "duration_hours": 10},
    {"id": "defi_surge", "title": "DeFi em Alta!", "description": "Protocolos de finanças descentralizadas explodem em valor", "icon": "flash", "color": "#E91E63", "effect": {"crypto": 1.25}, "duration_hours": 4},
]

@router.get("/market/events")
async def get_market_events(current_user: dict = Depends(get_current_user)):
    """Get current active market events"""
    now = datetime.utcnow()
    
    # Get active events
    active_events = await db.market_events.find({
        "expires_at": {"$gt": now}
    }).to_list(10)
    
    for e in active_events:
        if '_id' in e:
            del e['_id']
        if isinstance(e.get('expires_at'), datetime):
            e['seconds_remaining'] = int((e['expires_at'] - now).total_seconds())
            e['expires_at'] = e['expires_at'].isoformat()
        if isinstance(e.get('created_at'), datetime):
            e['created_at'] = e['created_at'].isoformat()
    
    return {
        "active_events": active_events,
        "count": len(active_events)
    }

@router.post("/market/trigger-event")
async def trigger_market_event(current_user: dict = Depends(get_current_user)):
    """Trigger a random market event (limited frequency)"""
    now = datetime.utcnow()
    
    # Check if an event was recently triggered (min 1 hour between events)
    last_event = await db.market_events.find_one({}, sort=[("created_at", -1)])
    if last_event:
        last_time = last_event.get('created_at', datetime.min)
        if isinstance(last_time, str):
            last_time = datetime.fromisoformat(last_time.replace('Z', '+00:00'))
        if (now - last_time).total_seconds() < 3600:
            mins_left = int((3600 - (now - last_time).total_seconds()) / 60)
            raise HTTPException(status_code=400, detail=f"Próximo evento em {mins_left} minutos")
    
    # Pick a random event
    event_template = random.choice(MARKET_EVENTS)
    
    event = {
        "id": str(uuid.uuid4()),
        "event_type": event_template['id'],
        "title": event_template['title'],
        "description": event_template['description'],
        "icon": event_template['icon'],
        "color": event_template['color'],
        "effect": event_template['effect'],
        "duration_hours": event_template['duration_hours'],
        "created_at": now,
        "expires_at": now + timedelta(hours=event_template['duration_hours']),
    }
    await db.market_events.insert_one(event)
    
    return {
        "success": True,
        "event": {k: v for k, v in event.items() if k != '_id'},
        "message": f"Evento: {event_template['title']}",
    }



