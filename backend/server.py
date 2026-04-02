from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
import uuid
from datetime import datetime, timedelta
import bcrypt
import jwt
from bson import ObjectId
import random
import math
import hashlib

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Configuration
JWT_SECRET = os.getenv('JWT_SECRET', 'your-super-secret-jwt-key-change-in-production')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_DAYS = 30

# Security
security = HTTPBearer()

# Create the main app without a prefix
app = FastAPI(title="Business Empire API")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# ==================== MODELS ====================

class Education(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    degree: str  # "Ensino Médio", "Graduação", "Mestrado", "Doutorado"
    field: str  # "Administração", "Tecnologia", etc.
    institution: str
    year_completed: int
    level: int  # 1-4 (médio=1, graduação=2, mestrado=3, doutorado=4)

class Certification(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    issuer: str
    date_obtained: datetime
    skill_boost: int  # quanto aumenta a habilidade (1-10)

class WorkExperience(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    company: str
    position: str
    start_date: datetime
    end_date: Optional[datetime] = None
    is_current: bool = False
    salary: float
    experience_gained: int  # pontos de experiência

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    password_hash: str
    name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Character Creation
    onboarding_completed: bool = False
    avatar_color: str = "green"  # green, blue, purple, orange, red, yellow
    avatar_icon: str = "person"  # Ionicons name
    avatar_photo: Optional[str] = None  # base64 encoded photo from gallery
    background: str = ""  # ex-militar, universitário, herdeiro, etc.
    dream: str = ""  # carreira, empreendedor, investidor, freelancer
    personality: dict = Field(default_factory=lambda: {
        "ambição": 5,  # 1-10
        "risco": 5,    # 1-10 (conservador vs arriscado)
        "social": 5,   # 1-10 (solitário vs social)
        "analítico": 5 # 1-10 (intuitivo vs analítico)
    })
    
    # Game Stats
    money: float = 1000.0  # Dinheiro inicial (varia por background)
    experience_points: int = 0
    level: int = 1
    location: str = "São Paulo, Brazil"  # Localização padrão
    
    # Currículo
    education: List[Education] = []
    certifications: List[Certification] = []
    work_experience: List[WorkExperience] = []
    skills: dict = Field(default_factory=lambda: {
        "liderança": 1,
        "comunicação": 1,
        "técnico": 1,
        "financeiro": 1,
        "negociação": 1
    })

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    token: str
    user: dict

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    onboarding_completed: bool = False
    avatar_color: str = "green"
    avatar_icon: str = "person"
    avatar_photo: Optional[str] = None
    background: str = ""
    dream: str = ""
    personality: dict = {}
    money: float = 1000.0
    experience_points: int = 0
    level: int = 1
    location: str = ""
    full_name: str = ""
    address: str = ""
    city: str = ""
    state: str = ""
    zip_code: str = ""
    phone: str = ""
    education: List[Education] = []
    certifications: List[Certification] = []
    work_experience: List[WorkExperience] = []
    skills: dict = {}
    created_at: Optional[datetime] = None

class EducationCreate(BaseModel):
    degree: str
    field: str
    institution: str
    year_completed: int
    level: int

class CertificationCreate(BaseModel):
    name: str
    issuer: str
    skill_boost: int

class CharacterProfileUpdate(BaseModel):
    avatar_color: str
    avatar_icon: str
    avatar_photo: Optional[str] = None  # base64 photo
    background: str
    dream: str
    personality: dict

class BackgroundOption(BaseModel):
    id: str
    name: str
    description: str
    money_bonus: float
    skill_bonuses: dict
    xp_multiplier: float

class DreamOption(BaseModel):
    id: str
    name: str
    description: str
    suggested_path: str

class Job(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    company: str
    description: str
    salary: float
    location: str
    requirements: dict = Field(default_factory=lambda: {
        "education_level": 1,  # 1-4
        "experience_months": 0,
        "skills": {}  # {"liderança": 3, "técnico": 5}
    })
    status: str = "open"  # open, closed
    created_at: datetime = Field(default_factory=datetime.utcnow)

class JobApplication(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    job_id: str
    status: str = "pending"  # pending, accepted, rejected
    match_score: float = 0.0
    applied_at: datetime = Field(default_factory=datetime.utcnow)

class Course(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    duration_hours: int
    cost: float
    skill_boost: dict = Field(default_factory=dict)  # {"técnico": 1}
    education_level_boost: int = 0  # 0 or 1
    category: str = "professional"  # professional, technical, management

class UserCourse(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    course_id: str
    completed: bool = False
    enrolled_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

class JobApplyRequest(BaseModel):
    job_id: str

class CourseEnrollRequest(BaseModel):
    course_id: str

class WorkRequest(BaseModel):
    hours: int = 8  # Horas trabalhadas

class AdBoost(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    multiplier: float = 1.0  # 1x, 2x, 3x, etc.
    ads_watched: int = 0
    expires_at: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)

class UserCourseComplete(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    course_id: str
    course_name: str
    completed_at: datetime = Field(default_factory=datetime.utcnow)
    earnings_boost: float  # Permanent boost percentage (e.g., 0.1 = 10%)

# ==================== HELPER FUNCTIONS ====================

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against a hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_token(user_id: str) -> str:
    """Create a JWT token"""
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(days=JWT_EXPIRATION_DAYS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def decode_token(token: str) -> dict:
    """Decode a JWT token"""
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Get current user from JWT token"""
    token = credentials.credentials
    payload = decode_token(token)
    user_id = payload.get('user_id')
    
    user = await db.users.find_one({'id': user_id})
    if not user:
        raise HTTPException(status_code=401, detail="Usuário não encontrado")
    
    return user

def calculate_level(experience_points: int) -> int:
    """Calculate user level based on experience points"""
    # Cada nível requer 1000 pontos de experiência
    return max(1, experience_points // 1000 + 1)

# ==================== ROUTES ====================

@api_router.get("/")
async def root():
    return {"message": "Business Empire API", "version": "1.0.0"}

# AUTH ROUTES
@api_router.post("/auth/register", response_model=TokenResponse)
async def register(user_data: UserCreate):
    """Register a new user"""
    # Check if user already exists
    existing_user = await db.users.find_one({'email': user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email já cadastrado")
    
    # Create new user
    user = User(
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        name=user_data.name
    )
    
    await db.users.insert_one(user.dict())
    
    # Create token
    token = create_token(user.id)
    
    # Return user without password hash
    user_dict = user.dict()
    del user_dict['password_hash']
    
    return TokenResponse(token=token, user=user_dict)

@api_router.post("/auth/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    """Login user"""
    user = await db.users.find_one({'email': credentials.email})
    if not user:
        raise HTTPException(status_code=401, detail="Email ou senha incorretos")
    
    if not verify_password(credentials.password, user['password_hash']):
        raise HTTPException(status_code=401, detail="Email ou senha incorretos")
    
    # Create token
    token = create_token(user['id'])
    
    # Return user without password hash
    del user['password_hash']
    del user['_id']
    
    return TokenResponse(token=token, user=user)

# USER ROUTES
@api_router.get("/user/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    """Get current user profile"""
    del current_user['password_hash']
    del current_user['_id']
    return current_user

@api_router.put("/user/avatar-photo")
async def update_avatar_photo(photo_data: dict, current_user: dict = Depends(get_current_user)):
    """Update user avatar photo"""
    await db.users.update_one(
        {'id': current_user['id']},
        {'$set': {'avatar_photo': photo_data.get('avatar_photo')}}
    )
    return {"message": "Foto atualizada com sucesso"}

@api_router.put("/user/personal-data")
async def update_personal_data(data: dict, current_user: dict = Depends(get_current_user)):
    """Update user personal data (name, address, phone, etc.)"""
    allowed = ['full_name', 'address', 'city', 'state', 'zip_code', 'phone', 'name', 'email', 'location']
    update_data = {k: v for k, v in data.items() if k in allowed and v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="Nenhum dado válido para atualizar")
    await db.users.update_one(
        {'id': current_user['id']},
        {'$set': update_data}
    )
    return {"message": "Dados pessoais atualizados com sucesso", "updated_fields": list(update_data.keys())}

@api_router.delete("/user/education/{education_id}")
async def delete_education(education_id: str, current_user: dict = Depends(get_current_user)):
    """Delete education entry"""
    await db.users.update_one(
        {'id': current_user['id']},
        {'$pull': {'education': {'id': education_id}}}
    )
    return {"message": "Educação removida com sucesso"}

@api_router.delete("/user/certification/{cert_id}")
async def delete_certification(cert_id: str, current_user: dict = Depends(get_current_user)):
    """Delete certification entry"""
    await db.users.update_one(
        {'id': current_user['id']},
        {'$pull': {'certifications': {'id': cert_id}}}
    )
    return {"message": "Certificação removida com sucesso"}

@api_router.put("/user/location")
async def update_location(location: dict, current_user: dict = Depends(get_current_user)):
    """Update user location"""
    await db.users.update_one(
        {'id': current_user['id']},
        {'$set': {'location': location['location']}}
    )
    return {"message": "Localização atualizada com sucesso", "location": location['location']}

# EDUCATION ROUTES
@api_router.post("/user/education")
async def add_education(education_data: EducationCreate, current_user: dict = Depends(get_current_user)):
    """Add education to user profile"""
    education = Education(**education_data.dict())
    
    # Add experience points based on education level
    exp_gain = education.level * 500
    
    # Update skills based on field
    skill_updates = {}
    if 'tecnologia' in education.field.lower() or 'engenharia' in education.field.lower():
        skill_updates['skills.técnico'] = min(10, current_user.get('skills', {}).get('técnico', 1) + education.level)
    elif 'administração' in education.field.lower() or 'negócios' in education.field.lower():
        skill_updates['skills.liderança'] = min(10, current_user.get('skills', {}).get('liderança', 1) + education.level)
        skill_updates['skills.financeiro'] = min(10, current_user.get('skills', {}).get('financeiro', 1) + education.level)
    elif 'comunicação' in education.field.lower():
        skill_updates['skills.comunicação'] = min(10, current_user.get('skills', {}).get('comunicação', 1) + education.level)
    
    new_exp = current_user.get('experience_points', 0) + exp_gain
    new_level = calculate_level(new_exp)
    
    await db.users.update_one(
        {'id': current_user['id']},
        {
            '$push': {'education': education.dict()},
            '$set': {
                'experience_points': new_exp,
                'level': new_level,
                **skill_updates
            }
        }
    )
    
    return {
        "message": "Educação adicionada com sucesso",
        "exp_gained": exp_gain,
        "new_level": new_level
    }

# CERTIFICATION ROUTES
@api_router.post("/user/certification")
async def add_certification(cert_data: CertificationCreate, current_user: dict = Depends(get_current_user)):
    """Add certification to user profile"""
    certification = Certification(
        **cert_data.dict(),
        date_obtained=datetime.utcnow()
    )
    
    # Add experience points
    exp_gain = cert_data.skill_boost * 100
    new_exp = current_user.get('experience_points', 0) + exp_gain
    new_level = calculate_level(new_exp)
    
    await db.users.update_one(
        {'id': current_user['id']},
        {
            '$push': {'certifications': certification.dict()},
            '$set': {
                'experience_points': new_exp,
                'level': new_level
            }
        }
    )
    
    return {
        "message": "Certificação adicionada com sucesso",
        "exp_gained": exp_gain,
        "new_level": new_level
    }

@api_router.get("/user/stats")
async def get_user_stats(current_user: dict = Depends(get_current_user)):
    """Get user statistics"""
    total_education = len(current_user.get('education', []))
    total_certifications = len(current_user.get('certifications', []))
    total_work_experience = len(current_user.get('work_experience', []))
    
    # Calculate total work experience in months
    months_experience = 0
    for exp in current_user.get('work_experience', []):
        start = exp.get('start_date')
        end = exp.get('end_date') or datetime.utcnow()
        if start is None:
            continue
        if isinstance(start, str):
            start = datetime.fromisoformat(start.replace('Z', '+00:00'))
        if isinstance(end, str):
            end = datetime.fromisoformat(end.replace('Z', '+00:00'))
        months_experience += (end.year - start.year) * 12 + (end.month - start.month)
    
    return {
        "level": current_user.get('level', 1),
        "experience_points": current_user.get('experience_points', 0),
        "next_level_exp": (current_user.get('level', 1) * 1000),
        "money": current_user.get('money', 1000),
        "education_count": total_education,
        "certification_count": total_certifications,
        "work_experience_count": total_work_experience,
        "months_experience": months_experience,
        "skills": current_user.get('skills', {})
    }

# CHARACTER CREATION ROUTES
@api_router.get("/character/backgrounds")
async def get_backgrounds():
    """Get available character backgrounds"""
    backgrounds = [
        {
            "id": "ex-militar",
            "name": "Ex-Militar",
            "description": "Disciplina e liderança forjadas no campo de batalha",
            "money_bonus": -200,  # Começa com R$ 800
            "skill_bonuses": {"liderança": 2, "negociação": 1},
            "xp_multiplier": 1.0
        },
        {
            "id": "universitario",
            "name": "Universitário",
            "description": "Conhecimento técnico e acadêmico",
            "money_bonus": -500,  # Começa com R$ 500
            "skill_bonuses": {"técnico": 2, "comunicação": 1},
            "xp_multiplier": 1.0
        },
        {
            "id": "herdeiro",
            "name": "Herdeiro",
            "description": "Nascido em berço de ouro, mas com muito a provar",
            "money_bonus": 4000,  # Começa com R$ 5.000
            "skill_bonuses": {"financeiro": 1},
            "xp_multiplier": 0.8  # Ganha menos XP de trabalho
        },
        {
            "id": "empreendedor",
            "name": "Empreendedor",
            "description": "Visão de negócios e networking",
            "money_bonus": 1000,  # Começa com R$ 2.000
            "skill_bonuses": {"negociação": 2, "liderança": 1},
            "xp_multiplier": 1.0
        },
        {
            "id": "autodidata",
            "name": "Autodidata",
            "description": "Aprendeu tudo sozinho, aprende rápido",
            "money_bonus": -400,  # Começa com R$ 600
            "skill_bonuses": {"técnico": 1},
            "xp_multiplier": 1.5  # Ganha 50% mais XP
        },
        {
            "id": "trabalhador",
            "name": "Trabalhador",
            "description": "Experiência prática e determinação",
            "money_bonus": 0,  # Começa com R$ 1.000
            "skill_bonuses": {"liderança": 1, "comunicação": 1},
            "xp_multiplier": 1.2  # Ganha 20% mais XP
        }
    ]
    return backgrounds

@api_router.get("/character/dreams")
async def get_dreams():
    """Get available character dreams/objectives"""
    dreams = [
        {
            "id": "carreira",
            "name": "Carreira Corporativa",
            "description": "Subir a hierarquia em grandes empresas",
            "suggested_path": "Foque em educação e certificações. Candidate-se a vagas em empresas estabelecidas."
        },
        {
            "id": "empreendedor",
            "name": "Empreendedor",
            "description": "Criar e gerenciar seus próprios negócios",
            "suggested_path": "Acumule capital, faça cursos de gestão e abra sua própria empresa."
        },
        {
            "id": "investidor",
            "name": "Investidor",
            "description": "Acumular patrimônio via investimentos",
            "suggested_path": "Estude o mercado financeiro e comece a investir cedo. Diversifique seu portfólio."
        },
        {
            "id": "freelancer",
            "name": "Freelancer/Consultor",
            "description": "Independência profissional e flexibilidade",
            "suggested_path": "Desenvolva habilidades especializadas e construa um portfólio forte."
        }
    ]
    return dreams

@api_router.post("/character/complete-profile")
async def complete_character_profile(
    profile_data: CharacterProfileUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Complete character profile after registration"""
    
    # Get background bonuses
    backgrounds = {
        "ex-militar": {"money": -200, "skills": {"liderança": 2, "negociação": 1}, "xp": 1.0},
        "universitario": {"money": -500, "skills": {"técnico": 2, "comunicação": 1}, "xp": 1.0},
        "herdeiro": {"money": 4000, "skills": {"financeiro": 1}, "xp": 0.8},
        "empreendedor": {"money": 1000, "skills": {"negociação": 2, "liderança": 1}, "xp": 1.0},
        "autodidata": {"money": -400, "skills": {"técnico": 1}, "xp": 1.5},
        "trabalhador": {"money": 0, "skills": {"liderança": 1, "comunicação": 1}, "xp": 1.2}
    }
    
    background_bonus = backgrounds.get(profile_data.background, {"money": 0, "skills": {}, "xp": 1.0})
    
    # Calculate new money
    new_money = 1000.0 + background_bonus["money"]
    
    # Update skills
    current_skills = current_user.get('skills', {
        "liderança": 1,
        "comunicação": 1,
        "técnico": 1,
        "financeiro": 1,
        "negociação": 1
    })
    
    for skill, bonus in background_bonus["skills"].items():
        if skill in current_skills:
            current_skills[skill] = min(10, current_skills[skill] + bonus)
    
    # Update user
    await db.users.update_one(
        {'id': current_user['id']},
        {
            '$set': {
                'onboarding_completed': True,
                'avatar_color': profile_data.avatar_color,
                'avatar_icon': profile_data.avatar_icon,
                'avatar_photo': profile_data.avatar_photo,
                'background': profile_data.background,
                'dream': profile_data.dream,
                'personality': profile_data.personality,
                'money': new_money,
                'skills': current_skills
            }
        }
    )
    
    return {
        "message": "Perfil completado com sucesso!",
        "money": new_money,
        "skills": current_skills,
        "xp_multiplier": background_bonus["xp"]
    }

# JOB SYSTEM ROUTES
@api_router.get("/jobs")
async def get_jobs(location: Optional[str] = None, min_salary: Optional[float] = None):
    """Get available job listings"""
    # Create some sample jobs if none exist
    job_count = await db.jobs.count_documents({})
    if job_count == 0:
        await seed_jobs()
    
    # Build query
    query = {"status": "open"}
    if location:
        query["location"] = {"$regex": location, "$options": "i"}
    if min_salary:
        query["salary"] = {"$gte": min_salary}
    
    jobs = await db.jobs.find(query).to_list(50)
    for job in jobs:
        del job['_id']
    
    return jobs

async def seed_jobs():
    """Create initial job listings"""
    jobs = [
        {
            "id": str(uuid.uuid4()),
            "title": "Assistente Administrativo",
            "company": "Tech Solutions Ltda",
            "description": "Auxiliar nas atividades administrativas e de escritório",
            "salary": 2500.0,
            "location": "São Paulo, Brazil",
            "requirements": {"education_level": 1, "experience_months": 0, "skills": {"comunicação": 2}},
            "status": "open",
            "created_at": datetime.utcnow()
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Analista de Sistemas Jr",
            "company": "Digital Innovations",
            "description": "Desenvolvimento e manutenção de sistemas",
            "salary": 4500.0,
            "location": "São Paulo, Brazil",
            "requirements": {"education_level": 2, "experience_months": 6, "skills": {"técnico": 4}},
            "status": "open",
            "created_at": datetime.utcnow()
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Gerente de Projetos",
            "company": "Corporate Solutions",
            "description": "Gerenciar equipes e projetos estratégicos",
            "salary": 8000.0,
            "location": "São Paulo, Brazil",
            "requirements": {"education_level": 2, "experience_months": 24, "skills": {"liderança": 5, "comunicação": 4}},
            "status": "open",
            "created_at": datetime.utcnow()
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Vendedor",
            "company": "ComercioMax",
            "description": "Vendas diretas e atendimento ao cliente",
            "salary": 2000.0,
            "location": "Rio de Janeiro, Brazil",
            "requirements": {"education_level": 1, "experience_months": 0, "skills": {"comunicação": 3, "negociação": 2}},
            "status": "open",
            "created_at": datetime.utcnow()
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Analista Financeiro",
            "company": "Invest Bank",
            "description": "Análise de investimentos e relatórios financeiros",
            "salary": 6000.0,
            "location": "São Paulo, Brazil",
            "requirements": {"education_level": 2, "experience_months": 12, "skills": {"financeiro": 5, "analítico": 4}},
            "status": "open",
            "created_at": datetime.utcnow()
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Estagiário",
            "company": "StartUp Hub",
            "description": "Apoio em diversas áreas da empresa",
            "salary": 1200.0,
            "location": "São Paulo, Brazil",
            "requirements": {"education_level": 2, "experience_months": 0, "skills": {}},
            "status": "open",
            "created_at": datetime.utcnow()
        }
    ]
    await db.jobs.insert_many(jobs)

# Higher-level jobs that unlock as player levels up
HIGHER_LEVEL_JOBS = [
    {"title": "Diretor de Marketing", "company": "Grupo Empresarial XYZ", "description": "Liderar estratégias de marketing digital e branding", "salary": 15000.0, "location": "São Paulo, Brazil", "requirements": {"education_level": 3, "experience_months": 36, "skills": {"comunicação": 6, "liderança": 5}}, "min_level": 10},
    {"title": "CTO (Chief Technology Officer)", "company": "TechVentures SA", "description": "Liderar equipe de tecnologia e inovação", "salary": 25000.0, "location": "São Paulo, Brazil", "requirements": {"education_level": 3, "experience_months": 48, "skills": {"técnico": 8, "liderança": 7}}, "min_level": 20},
    {"title": "VP de Vendas", "company": "MegaCorp Internacional", "description": "Vice-presidente responsável por vendas globais", "salary": 35000.0, "location": "São Paulo, Brazil", "requirements": {"education_level": 3, "experience_months": 60, "skills": {"negociação": 8, "liderança": 7, "comunicação": 6}}, "min_level": 30},
    {"title": "CEO", "company": "Holding Alpha", "description": "Diretor executivo de conglomerado empresarial", "salary": 50000.0, "location": "São Paulo, Brazil", "requirements": {"education_level": 3, "experience_months": 72, "skills": {"liderança": 9, "financeiro": 8, "negociação": 8}}, "min_level": 40},
    {"title": "Investidor Profissional", "company": "Capital Partners", "description": "Gestão de fundos e investimentos de alto valor", "salary": 80000.0, "location": "São Paulo, Brazil", "requirements": {"education_level": 3, "experience_months": 84, "skills": {"financeiro": 9, "negociação": 8}}, "min_level": 50},
    {"title": "Presidente do Conselho", "company": "Global Enterprises", "description": "Presidir conselho de administração de multinacional", "salary": 120000.0, "location": "São Paulo, Brazil", "requirements": {"education_level": 3, "experience_months": 96, "skills": {"liderança": 10, "financeiro": 9, "negociação": 9}}, "min_level": 60},
]

@api_router.get("/jobs/available-for-level")
async def get_jobs_for_level(current_user: dict = Depends(get_current_user)):
    """Get jobs including higher-level ones based on user level"""
    user = await db.users.find_one({"id": current_user['id']})
    user_level = user.get('level', 1)
    
    # Get base jobs
    base_jobs = await db.jobs.find({}).to_list(100)
    for j in base_jobs:
        if '_id' in j:
            del j['_id']
    
    # Add higher-level jobs the user qualifies for
    for hlj in HIGHER_LEVEL_JOBS:
        if user_level >= hlj['min_level']:
            job = {
                "id": f"hl_{hlj['title'].lower().replace(' ', '_')}",
                "title": hlj['title'],
                "company": hlj['company'],
                "description": hlj['description'],
                "salary": hlj['salary'],
                "location": hlj['location'],
                "requirements": hlj['requirements'],
                "status": "open",
                "min_level": hlj['min_level'],
                "is_premium": True,
                "created_at": datetime.utcnow().isoformat()
            }
            base_jobs.append(job)
    
    return base_jobs


@api_router.post("/jobs/apply")
async def apply_to_job(request: JobApplyRequest, current_user: dict = Depends(get_current_user)):
    """Apply to a job"""
    # Get job
    job = await db.jobs.find_one({"id": request.job_id})
    if not job:
        raise HTTPException(status_code=404, detail="Vaga não encontrada")
    
    # Check if already applied
    existing_application = await db.job_applications.find_one({
        "user_id": current_user['id'],
        "job_id": request.job_id
    })
    if existing_application:
        raise HTTPException(status_code=400, detail="Você já se candidatou a esta vaga")
    
    # Check if user already has a job
    current_job = await db.work_experiences.find_one({
        "user_id": current_user['id'],
        "is_current": True
    })
    if current_job:
        raise HTTPException(status_code=400, detail="Você já está empregado. Peça demissão primeiro.")
    
    # Calculate match score
    match_score = calculate_job_match(current_user, job['requirements'])
    
    # Auto-approve if match >= 70%
    status = "accepted" if match_score >= 70 else "pending"
    
    application = JobApplication(
        user_id=current_user['id'],
        job_id=request.job_id,
        status=status,
        match_score=match_score
    )
    
    await db.job_applications.insert_one(application.dict())
    
    # Remove ObjectId before returning
    if '_id' in job:
        del job['_id']
    
    return {
        "message": "Candidatura enviada!" if status == "pending" else "Parabéns! Você foi aprovado!",
        "status": status,
        "match_score": match_score,
        "job": job
    }

def calculate_job_match(user: dict, requirements: dict) -> float:
    """Calculate how well user matches job requirements"""
    score = 0
    max_score = 0
    
    # Check education level
    user_edu_level = 0
    for edu in user.get('education', []):
        user_edu_level = max(user_edu_level, edu.get('level', 0))
    
    req_edu = requirements.get('education_level', 0)
    if req_edu > 0:
        max_score += 30
        if user_edu_level >= req_edu:
            score += 30
        elif user_edu_level == req_edu - 1:
            score += 15
    
    # Check experience
    user_exp_months = 0
    for exp in user.get('work_experience', []):
        start = exp.get('start_date')
        end = exp.get('end_date') or datetime.utcnow()
        if start is None:
            continue
        if isinstance(start, str):
            start = datetime.fromisoformat(start.replace('Z', '+00:00'))
        if isinstance(end, str):
            end = datetime.fromisoformat(end.replace('Z', '+00:00'))
        user_exp_months += (end.year - start.year) * 12 + (end.month - start.month)
    
    req_exp = requirements.get('experience_months', 0)
    if req_exp > 0:
        max_score += 20
        if user_exp_months >= req_exp:
            score += 20
        elif user_exp_months >= req_exp * 0.7:
            score += 10
    
    # Check skills
    req_skills = requirements.get('skills', {})
    if req_skills:
        max_score += 50
        user_skills = user.get('skills', {})
        for skill, required_level in req_skills.items():
            user_level = user_skills.get(skill, 0)
            if user_level >= required_level:
                score += 50 / len(req_skills)
            elif user_level >= required_level * 0.7:
                score += 25 / len(req_skills)
    
    # If no requirements, 100% match
    if max_score == 0:
        return 100.0
    
    return (score / max_score) * 100

@api_router.post("/jobs/accept")
async def accept_job_offer(request: JobApplyRequest, current_user: dict = Depends(get_current_user)):
    """Accept a job offer and start working automatically"""
    # Get application
    application = await db.job_applications.find_one({
        "user_id": current_user['id'],
        "job_id": request.job_id,
        "status": "accepted"
    })
    
    if not application:
        raise HTTPException(status_code=404, detail="Oferta não encontrada ou não aprovada")
    
    # Get job
    job = await db.jobs.find_one({"id": request.job_id})
    
    # Create work experience entry
    work_exp = WorkExperience(
        company=job['company'],
        position=job['title'],
        start_date=datetime.utcnow(),
        is_current=True,
        salary=job['salary'],
        experience_gained=0
    )
    
    # Update user
    await db.users.update_one(
        {'id': current_user['id']},
        {'$push': {'work_experience': work_exp.dict()}}
    )
    
    # Store in separate collection for current job tracking
    await db.work_experiences.insert_one({
        **work_exp.dict(),
        "user_id": current_user['id'],
        "job_id": request.job_id,
        "days_worked": 0,
        "last_collection_date": datetime.utcnow()  # Track when user last collected earnings
    })
    
    return {
        "message": f"Parabéns! Você agora trabalha como {job['title']} na {job['company']}! Seus ganhos chegam automaticamente todos os dias.",
        "salary": job['salary'],
        "daily_earnings": job['salary'] / 30
    }

@api_router.get("/jobs/collect-earnings")
async def collect_earnings(current_user: dict = Depends(get_current_user)):
    """Collect accumulated earnings from current job"""
    # Get current job
    current_job = await db.work_experiences.find_one({
        "user_id": current_user['id'],
        "is_current": True
    })
    
    if not current_job:
        raise HTTPException(status_code=400, detail="Você não está empregado")
    
    # Calculate days since last collection
    last_collection = current_job.get('last_collection_date', current_job['start_date'])
    if isinstance(last_collection, str):
        last_collection = datetime.fromisoformat(last_collection.replace('Z', '+00:00'))
    
    now = datetime.utcnow()
    days_elapsed = (now - last_collection).total_seconds() / 86400  # Convert to days
    
    if days_elapsed < 0.001:  # Less than ~1.4 minutes
        return {
            "message": "Você já coletou seus ganhos recentemente. Aguarde pelo menos 1 minuto!",
            "earnings": 0,
            "days_elapsed": 0
        }
    
    # Calculate earnings (can accumulate multiple days)
    daily_salary = current_job['salary'] / 30
    total_earnings = daily_salary * days_elapsed
    
    # Apply ad boost multiplier if active
    boost_multiplier = 1.0
    ad_boost = await db.ad_boosts.find_one({"user_id": current_user['id']})
    if ad_boost:
        expires_at = ad_boost.get('expires_at')
        if expires_at and expires_at > now:
            boost_multiplier = ad_boost.get('multiplier', 1.0)
            total_earnings *= boost_multiplier
    
    # Apply courses earnings boost
    user_courses = await db.user_courses.find({"user_id": current_user['id']}).to_list(100)
    courses_boost = sum(c.get('earnings_boost', 0) for c in user_courses)
    if courses_boost > 0:
        total_earnings *= (1 + courses_boost)
    
    # Calculate XP gain
    xp_gain = int(80 * days_elapsed)
    
    # Update user money and XP
    new_money = current_user.get('money', 0) + total_earnings
    new_exp = current_user.get('experience_points', 0) + xp_gain
    new_level = calculate_level(new_exp)
    
    await db.users.update_one(
        {'id': current_user['id']},
        {
            '$set': {
                'money': new_money,
                'experience_points': new_exp,
                'level': new_level
            }
        }
    )
    
    # Update job tracking
    new_days_worked = current_job.get('days_worked', 0) + int(days_elapsed)
    await db.work_experiences.update_one(
        {'_id': current_job['_id']},
        {
            '$set': {
                'last_collection_date': now,
                'days_worked': new_days_worked
            }
        }
    )
    
    # Check for promotion (every 30 days, 10% raise)
    promotion_message = None
    if new_days_worked % 30 == 0 and new_days_worked > current_job.get('days_worked', 0):
        new_salary = current_job['salary'] * 1.1
        await db.work_experiences.update_one(
            {'_id': current_job['_id']},
            {'$set': {'salary': new_salary}}
        )
        promotion_message = f"Promoção! Seu salário aumentou para R$ {new_salary:.2f}/mês!"
    
    return {
        "message": f"Você coletou seus ganhos de {days_elapsed:.1f} dias de trabalho!",
        "earnings": round(total_earnings, 2),
        "xp_gained": xp_gain,
        "new_level": new_level,
        "new_money": round(new_money, 2),
        "days_elapsed": round(days_elapsed, 2),
        "days_worked": new_days_worked,
        "boost_multiplier": boost_multiplier,
        "courses_boost": round(courses_boost, 2),
        "promotion": promotion_message
    }

@api_router.post("/jobs/resign")
async def resign_from_job(current_user: dict = Depends(get_current_user)):
    """Resign from current job"""
    current_job = await db.work_experiences.find_one({
        "user_id": current_user['id'],
        "is_current": True
    })
    
    if not current_job:
        raise HTTPException(status_code=400, detail="Você não está empregado")
    
    # Update work experience to mark as ended
    await db.work_experiences.update_one(
        {'_id': current_job['_id']},
        {
            '$set': {
                'is_current': False,
                'end_date': datetime.utcnow()
            }
        }
    )
    
    # Update user's work_experience array
    await db.users.update_one(
        {
            'id': current_user['id'],
            'work_experience.id': current_job['id']
        },
        {
            '$set': {
                'work_experience.$.is_current': False,
                'work_experience.$.end_date': datetime.utcnow()
            }
        }
    )
    
    return {"message": "Você pediu demissão. Boa sorte na próxima oportunidade!"}

# ADS BOOST SYSTEM
@api_router.post("/ads/watch")
async def watch_ad(current_user: dict = Depends(get_current_user)):
    """Watch an ad to boost earnings (simulated)"""
    # Check if user has active job
    current_job = await db.work_experiences.find_one({
        "user_id": current_user['id'],
        "is_current": True
    })
    
    if not current_job:
        raise HTTPException(status_code=400, detail="Você precisa ter um emprego para assistir propagandas")
    
    # Get or create ad boost
    ad_boost = await db.ad_boosts.find_one({"user_id": current_user['id']})
    
    now = datetime.utcnow()
    
    if ad_boost:
        # Check if expired
        expires_at = ad_boost.get('expires_at')
        if isinstance(expires_at, str):
            expires_at = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
        
        if expires_at > now:
            # Still active, increase multiplier and reset timer to 1 hour
            new_multiplier = min(10.0, ad_boost.get('multiplier', 1.0) + 1.0)
            new_ads_watched = ad_boost.get('ads_watched', 0) + 1
            new_expires_at = now + timedelta(hours=1)
        else:
            # Expired, reset to 2x with fresh 1 hour
            new_multiplier = 2.0
            new_ads_watched = 1
            new_expires_at = now + timedelta(hours=1)
        
        await db.ad_boosts.update_one(
            {'_id': ad_boost['_id']},
            {
                '$set': {
                    'multiplier': new_multiplier,
                    'ads_watched': new_ads_watched,
                    'expires_at': new_expires_at
                }
            }
        )
    else:
        # Create new boost - 1 hour duration
        new_multiplier = 2.0
        new_ads_watched = 1
        new_expires_at = now + timedelta(hours=1)
        
        boost = AdBoost(
            user_id=current_user['id'],
            multiplier=new_multiplier,
            ads_watched=new_ads_watched,
            expires_at=new_expires_at
        )
        await db.ad_boosts.insert_one(boost.dict())
    
    # Calculate boosted daily earnings
    daily_salary = current_job['salary'] / 30
    boosted_daily = daily_salary * new_multiplier
    seconds_remaining = int((new_expires_at - now).total_seconds())
    
    return {
        "message": f"Propaganda assistida! Seus ganhos aumentaram {new_multiplier}x por 1 hora!",
        "multiplier": new_multiplier,
        "ads_watched": new_ads_watched,
        "expires_at": new_expires_at.isoformat(),
        "seconds_remaining": seconds_remaining,
        "daily_earnings_normal": daily_salary,
        "daily_earnings_boosted": boosted_daily,
        "boost_value": boosted_daily - daily_salary
    }

@api_router.get("/ads/current-boost")
async def get_current_boost(current_user: dict = Depends(get_current_user)):
    """Get current ad boost status"""
    ad_boost = await db.ad_boosts.find_one({"user_id": current_user['id']})
    
    if not ad_boost:
        return {
            "active": False,
            "multiplier": 1.0,
            "ads_watched": 0,
            "seconds_remaining": 0
        }
    
    now = datetime.utcnow()
    expires_at = ad_boost.get('expires_at')
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
    
    if expires_at <= now:
        # Expired
        return {
            "active": False,
            "multiplier": 1.0,
            "ads_watched": 0,
            "seconds_remaining": 0
        }
    
    seconds_remaining = int((expires_at - now).total_seconds())
    # Multiplier stays constant for the full duration (no decay)
    current_multiplier = ad_boost.get('multiplier', 1.0)
    
    return {
        "active": True,
        "multiplier": current_multiplier,
        "max_multiplier": current_multiplier,
        "ads_watched": ad_boost.get('ads_watched', 0),
        "seconds_remaining": seconds_remaining,
        "expires_at": expires_at.isoformat()
    }

@api_router.get("/jobs/my-applications")
async def get_my_applications(current_user: dict = Depends(get_current_user)):
    """Get user's job applications"""
    applications = await db.job_applications.find({"user_id": current_user['id']}).to_list(100)
    
    # Enrich with job details
    for app in applications:
        job = await db.jobs.find_one({"id": app['job_id']})
        if job and '_id' in job:
            del job['_id']
        app['job'] = job
        if '_id' in app:
            del app['_id']
    
    return applications

@api_router.get("/jobs/current")
async def get_current_job(current_user: dict = Depends(get_current_user)):
    """Get user's current job"""
    current_job = await db.work_experiences.find_one({
        "user_id": current_user['id'],
        "is_current": True
    })
    
    if not current_job:
        return None
    
    # Get job details
    job = await db.jobs.find_one({"id": current_job.get('job_id')})
    if job and '_id' in job:
        del job['_id']
    current_job['job_details'] = job
    if '_id' in current_job:
        del current_job['_id']
    
    return current_job

# COURSES SYSTEM
@api_router.get("/courses")
async def get_courses():
    """Get available courses - Harvard-inspired real courses"""
    courses = [
        # Level 1-5: Basic courses
        {
            "id": "cs50-intro",
            "name": "CS50: Intro to Computer Science",
            "description": "Curso de Harvard - Fundamentos de programação e pensamento computacional",
            "institution": "Harvard University",
            "cost": 500,
            "earnings_boost": 0.08,
            "skill_boost": {"técnico": 1},
            "duration": "Instantâneo",
            "level_required": 1,
            "category": "tecnologia",
            "icon": "laptop",
        },
        {
            "id": "excel-avancado",
            "name": "Excel & Análise de Dados",
            "description": "Domine planilhas, fórmulas avançadas e automação com VBA",
            "institution": "MIT OpenCourseWare",
            "cost": 600,
            "earnings_boost": 0.10,
            "skill_boost": {"técnico": 1},
            "duration": "Instantâneo",
            "level_required": 1,
            "category": "tecnologia",
            "icon": "grid",
        },
        {
            "id": "negotiation-mastery",
            "name": "Negociação e Persuasão",
            "description": "Técnicas de negociação de alto impacto - Yale School of Management",
            "institution": "Yale University",
            "cost": 700,
            "earnings_boost": 0.12,
            "skill_boost": {"negociação": 2},
            "duration": "Instantâneo",
            "level_required": 2,
            "category": "negocios",
            "icon": "people",
        },
        {
            "id": "financial-markets",
            "name": "Financial Markets",
            "description": "Curso de Robert Shiller sobre mercados financeiros globais",
            "institution": "Yale University",
            "cost": 800,
            "earnings_boost": 0.12,
            "skill_boost": {"financeiro": 2},
            "duration": "Instantâneo",
            "level_required": 3,
            "category": "financas",
            "icon": "trending-up",
        },
        {
            "id": "ingles-negocios",
            "name": "Business English Communication",
            "description": "Comunicação profissional internacional para executivos",
            "institution": "Cambridge University",
            "cost": 900,
            "earnings_boost": 0.15,
            "skill_boost": {"comunicação": 2},
            "duration": "Instantâneo",
            "level_required": 3,
            "category": "comunicacao",
            "icon": "language",
        },
        # Level 5-10: Intermediate courses
        {
            "id": "gestao-projetos",
            "name": "Gestão de Projetos (PMP/Agile)",
            "description": "Metodologias ágeis, Scrum, Kanban e PMBOK - Stanford Online",
            "institution": "Stanford University",
            "cost": 1500,
            "earnings_boost": 0.18,
            "skill_boost": {"liderança": 2},
            "duration": "Instantâneo",
            "level_required": 5,
            "category": "gestao",
            "icon": "clipboard",
        },
        {
            "id": "analise-dados",
            "name": "Data Science & Machine Learning",
            "description": "Python, Power BI, ML e visualização de dados avançada",
            "institution": "Harvard University",
            "cost": 2000,
            "earnings_boost": 0.22,
            "skill_boost": {"técnico": 2, "financeiro": 1},
            "duration": "Instantâneo",
            "level_required": 7,
            "category": "tecnologia",
            "icon": "analytics",
        },
        {
            "id": "marketing-digital",
            "name": "Digital Marketing Strategy",
            "description": "SEO, Growth Hacking, Social Media e funis de conversão",
            "institution": "Wharton School (UPenn)",
            "cost": 1800,
            "earnings_boost": 0.20,
            "skill_boost": {"comunicação": 2, "negociação": 1},
            "duration": "Instantâneo",
            "level_required": 8,
            "category": "negocios",
            "icon": "megaphone",
        },
        # Level 10-20: Advanced courses
        {
            "id": "lideranca-estrategica",
            "name": "Strategic Leadership & Management",
            "description": "MBA executivo resumido - liderança em ambientes complexos",
            "institution": "Harvard Business School",
            "cost": 3500,
            "earnings_boost": 0.30,
            "skill_boost": {"liderança": 3, "financeiro": 1},
            "duration": "Instantâneo",
            "level_required": 10,
            "category": "gestao",
            "icon": "trophy",
        },
        {
            "id": "private-equity",
            "name": "Private Equity & Venture Capital",
            "description": "Análise de investimentos, valuation e fundraising",
            "institution": "Harvard Business School",
            "cost": 4000,
            "earnings_boost": 0.28,
            "skill_boost": {"financeiro": 3},
            "duration": "Instantâneo",
            "level_required": 12,
            "category": "financas",
            "icon": "cash",
        },
        {
            "id": "innovation-entrepreneurship",
            "name": "Innovation & Entrepreneurship",
            "description": "De startup a IPO - metodologia Lean e Design Thinking",
            "institution": "MIT Sloan",
            "cost": 5000,
            "earnings_boost": 0.35,
            "skill_boost": {"liderança": 2, "técnico": 2},
            "duration": "Instantâneo",
            "level_required": 15,
            "category": "negocios",
            "icon": "bulb",
        },
        # Level 20+: Elite courses
        {
            "id": "global-economics",
            "name": "Global Economics & Policy",
            "description": "Macroeconomia global, políticas monetárias e geopolítica",
            "institution": "Harvard Kennedy School",
            "cost": 8000,
            "earnings_boost": 0.40,
            "skill_boost": {"financeiro": 3, "comunicação": 2},
            "duration": "Instantâneo",
            "level_required": 20,
            "category": "financas",
            "icon": "globe",
        },
        {
            "id": "corporate-governance",
            "name": "Corporate Governance & Ethics",
            "description": "Governança corporativa, compliance e ESG para CEOs",
            "institution": "Stanford GSB",
            "cost": 10000,
            "earnings_boost": 0.45,
            "skill_boost": {"liderança": 3, "negociação": 2},
            "duration": "Instantâneo",
            "level_required": 25,
            "category": "gestao",
            "icon": "shield-checkmark",
        },
        {
            "id": "executive-mba",
            "name": "Executive MBA Program",
            "description": "Programa completo de MBA executivo - o curso definitivo",
            "institution": "Harvard Business School",
            "cost": 25000,
            "earnings_boost": 0.60,
            "skill_boost": {"liderança": 3, "financeiro": 3, "comunicação": 2, "negociação": 2},
            "duration": "Instantâneo",
            "level_required": 40,
            "category": "gestao",
            "icon": "school",
        },
    ]
    return courses

@api_router.post("/courses/enroll")
async def enroll_course(request: CourseEnrollRequest, current_user: dict = Depends(get_current_user)):
    """Enroll in a course"""
    # Check if already completed
    existing = await db.user_courses.find_one({
        "user_id": current_user['id'],
        "course_id": request.course_id
    })
    
    if existing:
        raise HTTPException(status_code=400, detail="Você já fez este curso!")
    
    # Get course details from the full courses list
    all_courses = (await get_courses())
    course = next((c for c in all_courses if c['id'] == request.course_id), None)
    if not course:
        raise HTTPException(status_code=404, detail="Curso não encontrado")
    
    # Check level requirement
    user_level = current_user.get('level', 1)
    if user_level < course.get('level_required', 1):
        raise HTTPException(status_code=400, detail=f"Requer nível {course['level_required']}. Seu nível: {user_level}")
    
    # Check if user has enough money
    if current_user.get('money', 0) < course['cost']:
        raise HTTPException(status_code=400, detail="Dinheiro insuficiente!")
    
    # Deduct cost
    new_money = current_user.get('money', 0) - course['cost']
    
    # Update skills
    current_skills = current_user.get('skills', {})
    for skill, boost in course['skill_boost'].items():
        if skill in current_skills:
            current_skills[skill] = min(10, current_skills[skill] + boost)
    
    # Update user
    await db.users.update_one(
        {'id': current_user['id']},
        {
            '$set': {
                'money': new_money,
                'skills': current_skills
            }
        }
    )
    
    # Save course completion
    course_complete = UserCourseComplete(
        user_id=current_user['id'],
        course_id=course['id'],
        course_name=course['name'],
        earnings_boost=course['earnings_boost']
    )
    await db.user_courses.insert_one(course_complete.dict())
    
    return {
        "message": f"Curso '{course['name']}' concluído!",
        "cost": course['cost'],
        "earnings_boost": f"+{course['earnings_boost']*100}%",
        "skill_boost": course['skill_boost'],
        "new_money": new_money
    }

@api_router.get("/courses/my-courses")
async def get_my_courses(current_user: dict = Depends(get_current_user)):
    """Get user's completed courses"""
    courses = await db.user_courses.find({"user_id": current_user['id']}).to_list(100)
    
    for course in courses:
        del course['_id']
    
    # Calculate total boost
    total_boost = sum(c.get('earnings_boost', 0) for c in courses)
    
    return {
        "courses": courses,
        "total_boost": total_boost,
        "total_boost_percentage": f"{total_boost * 100}%"
    }

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
    {"ticker": "PETR4", "name": "Petrobras PN", "category": "acoes", "base_price": 38.50, "volatility": 2.5, "trend": 0.05, "description": "Petróleo Brasileiro S.A. - Ação preferencial", "sector": "Petróleo & Gás", "market_cap": "R$ 500B"},
    {"ticker": "VALE3", "name": "Vale ON", "category": "acoes", "base_price": 62.00, "volatility": 2.8, "trend": 0.03, "description": "Vale S.A. - Mineração e metais", "sector": "Mineração", "market_cap": "R$ 280B"},
    {"ticker": "ITUB4", "name": "Itaú Unibanco PN", "category": "acoes", "base_price": 32.00, "volatility": 1.8, "trend": 0.04, "description": "Itaú Unibanco - Maior banco privado do Brasil", "sector": "Financeiro", "market_cap": "R$ 300B"},
    {"ticker": "BBDC4", "name": "Bradesco PN", "category": "acoes", "base_price": 14.50, "volatility": 2.2, "trend": -0.02, "description": "Banco Bradesco S.A.", "sector": "Financeiro", "market_cap": "R$ 150B"},
    {"ticker": "WEGE3", "name": "WEG ON", "category": "acoes", "base_price": 44.00, "volatility": 2.0, "trend": 0.06, "description": "WEG S.A. - Motores e equipamentos elétricos", "sector": "Industrial", "market_cap": "R$ 185B"},
    {"ticker": "MGLU3", "name": "Magazine Luiza ON", "category": "acoes", "base_price": 2.80, "volatility": 5.0, "trend": -0.08, "description": "Magazine Luiza - E-commerce e varejo", "sector": "Varejo", "market_cap": "R$ 18B"},
    {"ticker": "ABEV3", "name": "Ambev ON", "category": "acoes", "base_price": 13.20, "volatility": 1.5, "trend": 0.02, "description": "Ambev S.A. - Maior cervejaria da América Latina", "sector": "Bebidas", "market_cap": "R$ 210B"},
    {"ticker": "B3SA3", "name": "B3 ON", "category": "acoes", "base_price": 12.50, "volatility": 2.3, "trend": 0.01, "description": "B3 S.A. - Bolsa de Valores do Brasil", "sector": "Financeiro", "market_cap": "R$ 70B"},
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

@app.on_event("startup")
async def startup_investments():
    await seed_investments()

# Investment Endpoints
@api_router.get("/investments/market")
async def get_market(category: Optional[str] = None, current_user: dict = Depends(get_current_user)):
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

@api_router.get("/investments/asset/{asset_id}/history")
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

@api_router.post("/investments/buy")
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
            detail=f"Saldo insuficiente. Necessário: R$ {total_cost:.2f}, Disponível: R$ {user['money']:.2f}"
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

@api_router.post("/investments/sell")
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
    
    profit_msg = f"Lucro: R$ {profit:.2f}" if profit >= 0 else f"Prejuízo: R$ {abs(profit):.2f}"
    
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

@api_router.get("/investments/portfolio")
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

@api_router.get("/investments/transactions")
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

# ==================== MAP / COMPANIES SYSTEM ====================

MAP_COMPANY_SEEDS = [
    # São Paulo - Centro
    {"name": "TechNova Solutions", "category": "tecnologia", "lat": -23.5505, "lng": -46.6333, "description": "Startup de IA e Machine Learning", "employees": 120, "revenue": "R$ 15M/ano", "rating": 4.5, "city": "São Paulo"},
    {"name": "Banco Digital Plus", "category": "financeiro", "lat": -23.5475, "lng": -46.6361, "description": "Fintech de pagamentos digitais", "employees": 450, "revenue": "R$ 200M/ano", "rating": 4.2, "city": "São Paulo"},
    {"name": "Café Paulistano", "category": "alimentacao", "lat": -23.5565, "lng": -46.6297, "description": "Rede de cafeterias premium", "employees": 85, "revenue": "R$ 8M/ano", "rating": 4.7, "city": "São Paulo"},
    {"name": "Construtora Horizonte", "category": "construcao", "lat": -23.5615, "lng": -46.6555, "description": "Construtora de edifícios residenciais", "employees": 800, "revenue": "R$ 500M/ano", "rating": 3.9, "city": "São Paulo"},
    # São Paulo - Faria Lima
    {"name": "Venture Capital BR", "category": "financeiro", "lat": -23.5735, "lng": -46.6895, "description": "Fundo de investimento em startups", "employees": 35, "revenue": "R$ 2B AUM", "rating": 4.8, "city": "São Paulo"},
    {"name": "E-Commerce Master", "category": "varejo", "lat": -23.5750, "lng": -46.6850, "description": "Marketplace líder em eletrônicos", "employees": 2000, "revenue": "R$ 1.2B/ano", "rating": 4.0, "city": "São Paulo"},
    {"name": "GreenEnergy Ltda", "category": "energia", "lat": -23.5685, "lng": -46.6920, "description": "Energia solar e sustentável", "employees": 200, "revenue": "R$ 45M/ano", "rating": 4.3, "city": "São Paulo"},
    # São Paulo - Vila Olímpia
    {"name": "AppFactory Studio", "category": "tecnologia", "lat": -23.5950, "lng": -46.6800, "description": "Desenvolvimento de aplicativos mobile", "employees": 60, "revenue": "R$ 12M/ano", "rating": 4.6, "city": "São Paulo"},
    {"name": "FitLife Academias", "category": "saude", "lat": -23.5920, "lng": -46.6755, "description": "Rede de academias premium", "employees": 350, "revenue": "R$ 30M/ano", "rating": 4.1, "city": "São Paulo"},
    # São Paulo - Pinheiros
    {"name": "Agência Criativa 360", "category": "marketing", "lat": -23.5620, "lng": -46.6910, "description": "Marketing digital e branding", "employees": 40, "revenue": "R$ 6M/ano", "rating": 4.4, "city": "São Paulo"},
    {"name": "Restaurante Sabores", "category": "alimentacao", "lat": -23.5630, "lng": -46.6935, "description": "Gastronomia contemporânea brasileira", "employees": 25, "revenue": "R$ 3M/ano", "rating": 4.9, "city": "São Paulo"},
    # Rio de Janeiro
    {"name": "Petro Energy RJ", "category": "energia", "lat": -22.9068, "lng": -43.1729, "description": "Exploração de petróleo offshore", "employees": 5000, "revenue": "R$ 10B/ano", "rating": 3.8, "city": "Rio de Janeiro"},
    {"name": "TurismoRio Ltda", "category": "turismo", "lat": -22.9519, "lng": -43.2105, "description": "Turismo e hotelaria", "employees": 150, "revenue": "R$ 20M/ano", "rating": 4.0, "city": "Rio de Janeiro"},
    {"name": "GameStudio Carioca", "category": "tecnologia", "lat": -22.9137, "lng": -43.1764, "description": "Estúdio de jogos indie", "employees": 30, "revenue": "R$ 4M/ano", "rating": 4.7, "city": "Rio de Janeiro"},
    # Belo Horizonte
    {"name": "MineralTech", "category": "mineracao", "lat": -19.9167, "lng": -43.9345, "description": "Tecnologia para mineração sustentável", "employees": 280, "revenue": "R$ 80M/ano", "rating": 4.1, "city": "Belo Horizonte"},
    {"name": "Padaria Mineira Real", "category": "alimentacao", "lat": -19.9200, "lng": -43.9380, "description": "Padaria artesanal mineira", "employees": 15, "revenue": "R$ 1.5M/ano", "rating": 4.8, "city": "Belo Horizonte"},
    # Curitiba
    {"name": "LogiTech Transportes", "category": "logistica", "lat": -25.4284, "lng": -49.2733, "description": "Logística e transporte rodoviário", "employees": 600, "revenue": "R$ 150M/ano", "rating": 3.7, "city": "Curitiba"},
    {"name": "BioFarm Labs", "category": "saude", "lat": -25.4320, "lng": -49.2700, "description": "Pesquisa farmacêutica e biotecnologia", "employees": 90, "revenue": "R$ 25M/ano", "rating": 4.5, "city": "Curitiba"},
    # Porto Alegre
    {"name": "AgroSul Grãos", "category": "agronegocio", "lat": -30.0346, "lng": -51.2177, "description": "Produção e exportação de grãos", "employees": 400, "revenue": "R$ 300M/ano", "rating": 4.0, "city": "Porto Alegre"},
    {"name": "DesignGaúcho Studio", "category": "marketing", "lat": -30.0300, "lng": -51.2200, "description": "Design e UX para produtos digitais", "employees": 20, "revenue": "R$ 2M/ano", "rating": 4.6, "city": "Porto Alegre"},
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
                "open_positions": random.randint(0, 5),
                "investment_available": random.choice([True, False]),
                "min_investment": random.choice([5000, 10000, 25000, 50000, 100000]),
                "created_at": datetime.utcnow(),
            }
            companies.append(company)
        await db.map_companies.insert_many(companies)
        logger.info(f"Seeded {len(companies)} map companies")

@app.on_event("startup")
async def startup_map():
    await seed_map_companies()

@api_router.get("/map/companies")
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

@api_router.get("/map/companies/{company_id}")
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
    {"name": "Lanchonete do Zé", "segment": "restaurante", "price": 15000, "monthly_revenue": 3000, "employees": 5, "description": "Lanchonete de bairro com clientela fiel", "level_required": 1},
    {"name": "Pizzaria Bella Napoli", "segment": "restaurante", "price": 80000, "monthly_revenue": 12000, "employees": 15, "description": "Pizzaria italiana com forno a lenha", "level_required": 3},
    {"name": "Rede Burger Premium", "segment": "restaurante", "price": 500000, "monthly_revenue": 65000, "employees": 80, "description": "Rede de hamburguerias com 5 unidades", "level_required": 8},
    # Lojas
    {"name": "Bazar Popular", "segment": "loja", "price": 10000, "monthly_revenue": 2000, "employees": 3, "description": "Loja de variedades no centro", "level_required": 1},
    {"name": "Boutique Fashion", "segment": "loja", "price": 120000, "monthly_revenue": 18000, "employees": 8, "description": "Loja de roupas de grife", "level_required": 4},
    {"name": "Mega Store Eletrônicos", "segment": "loja", "price": 800000, "monthly_revenue": 90000, "employees": 50, "description": "Loja de eletrônicos e tecnologia", "level_required": 10},
    # Tecnologia
    {"name": "Dev Studio Indie", "segment": "tecnologia", "price": 50000, "monthly_revenue": 8000, "employees": 4, "description": "Estúdio de desenvolvimento de apps", "level_required": 2},
    {"name": "SaaS Analytics Pro", "segment": "tecnologia", "price": 300000, "monthly_revenue": 45000, "employees": 20, "description": "Plataforma SaaS de analytics", "level_required": 6},
    {"name": "CyberTech Security", "segment": "tecnologia", "price": 1500000, "monthly_revenue": 180000, "employees": 100, "description": "Empresa de cibersegurança corporativa", "level_required": 12},
    # Fábricas
    {"name": "Confecção Básica", "segment": "fabrica", "price": 60000, "monthly_revenue": 10000, "employees": 20, "description": "Fábrica de camisetas e uniformes", "level_required": 3},
    {"name": "Fábrica de Móveis Artesanais", "segment": "fabrica", "price": 250000, "monthly_revenue": 35000, "employees": 40, "description": "Produção de móveis sob medida", "level_required": 5},
    {"name": "Indústria Metalúrgica", "segment": "fabrica", "price": 2000000, "monthly_revenue": 250000, "employees": 200, "description": "Produção de peças industriais", "level_required": 15},
    # Saúde
    {"name": "Farmácia Comunitária", "segment": "saude", "price": 40000, "monthly_revenue": 7000, "employees": 6, "description": "Farmácia de bairro com manipulação", "level_required": 2},
    {"name": "Clínica Odontológica", "segment": "saude", "price": 200000, "monthly_revenue": 30000, "employees": 12, "description": "Clínica odontológica especializada", "level_required": 5},
    # Educação
    {"name": "Escola de Idiomas", "segment": "educacao", "price": 35000, "monthly_revenue": 6000, "employees": 8, "description": "Escola de inglês e espanhol", "level_required": 2},
    {"name": "Faculdade TechEdu", "segment": "educacao", "price": 1000000, "monthly_revenue": 120000, "employees": 60, "description": "Faculdade de tecnologia EAD", "level_required": 10},
    # Entretenimento
    {"name": "Lan House Gamer", "segment": "entretenimento", "price": 25000, "monthly_revenue": 4500, "employees": 3, "description": "Espaço gamer com PCs de alta performance", "level_required": 1},
    {"name": "Parque Aquático Splash", "segment": "entretenimento", "price": 3000000, "monthly_revenue": 350000, "employees": 150, "description": "Parque aquático com atrações radicais", "level_required": 15},
    # Imobiliária
    {"name": "Imobiliária Local", "segment": "imobiliaria", "price": 70000, "monthly_revenue": 11000, "employees": 5, "description": "Imobiliária focada em aluguéis", "level_required": 3},
    {"name": "Construtora Horizonte", "segment": "imobiliaria", "price": 5000000, "monthly_revenue": 500000, "employees": 300, "description": "Construtora de prédios residenciais", "level_required": 18},
    # Logística
    {"name": "Motoboy Express", "segment": "logistica", "price": 20000, "monthly_revenue": 3500, "employees": 10, "description": "Serviço de entregas rápidas", "level_required": 1},
    {"name": "TransBR Cargas", "segment": "logistica", "price": 600000, "monthly_revenue": 75000, "employees": 45, "description": "Transportadora rodoviária nacional", "level_required": 8},
    # Agronegócio
    {"name": "Horta Orgânica", "segment": "agronegocio", "price": 18000, "monthly_revenue": 3200, "employees": 4, "description": "Produção de hortaliças orgânicas", "level_required": 1},
    {"name": "Fazenda Boi Gordo", "segment": "agronegocio", "price": 2500000, "monthly_revenue": 280000, "employees": 50, "description": "Fazenda de gado de corte premium", "level_required": 12},
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

@app.on_event("startup")
async def startup_companies():
    await seed_companies_for_sale()

@api_router.get("/companies/segments")
async def get_segments(current_user: dict = Depends(get_current_user)):
    return COMPANY_SEGMENTS

@api_router.get("/companies/available")
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

@api_router.post("/companies/buy")
async def buy_company(request: dict, current_user: dict = Depends(get_current_user)):
    company_id = request.get('company_id')
    company = await db.companies_for_sale.find_one({"id": company_id})
    if not company:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    user = await db.users.find_one({"id": current_user['id']})
    if user['money'] < company['price']:
        raise HTTPException(status_code=400, detail=f"Saldo insuficiente. Necessário: R$ {company['price']:,.2f}")
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
        "monthly_revenue": company['monthly_revenue'],
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
        "monthly_revenue": company['monthly_revenue'],
        "new_balance": round(new_money, 2),
    }

@api_router.post("/companies/create")
async def create_company(request: CreateCompanyRequest, current_user: dict = Depends(get_current_user)):
    if request.segment not in COMPANY_SEGMENTS:
        raise HTTPException(status_code=400, detail="Segmento inválido")
    user = await db.users.find_one({"id": current_user['id']})
    creation_cost = 5000
    if user['money'] < creation_cost:
        raise HTTPException(status_code=400, detail=f"Saldo insuficiente. Custo de criação: R$ {creation_cost:,.2f}")
    new_money = user['money'] - creation_cost
    await db.users.update_one({"id": current_user['id']}, {"$set": {"money": new_money}})
    seg = COMPANY_SEGMENTS[request.segment]
    base_revenue = random.randint(800, 2500)
    user_company = {
        "id": str(uuid.uuid4()),
        "user_id": current_user['id'],
        "source_company_id": None,
        "name": request.name,
        "segment": request.segment,
        "icon": seg['icon'],
        "color": seg['color'],
        "monthly_revenue": base_revenue,
        "employees": random.randint(1, 5),
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
        "company": {"name": request.name, "segment": request.segment, "monthly_revenue": base_revenue},
        "new_balance": round(new_money, 2),
    }

@api_router.get("/companies/owned")
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
        c['effective_revenue'] = round(c['monthly_revenue'] * effective_mult)
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
        total_monthly += c['effective_revenue']
    return {"companies": companies, "total_monthly_revenue": total_monthly, "count": len(companies)}

@api_router.post("/companies/collect-revenue")
async def collect_company_revenue(current_user: dict = Depends(get_current_user)):
    companies = await db.user_companies.find({"user_id": current_user['id']}).to_list(200)
    if not companies:
        raise HTTPException(status_code=400, detail="Você não possui empresas")
    now = datetime.utcnow()
    total_revenue = 0
    details = []
    for c in companies:
        last = c.get('last_collection', now)
        if isinstance(last, str):
            last = datetime.fromisoformat(last.replace('Z', '+00:00'))
        days = (now - last).total_seconds() / 86400
        if days < 0.001:
            continue
        daily_rev = c['monthly_revenue'] / 30
        boost_active = c.get('ad_boost_expires') and c['ad_boost_expires'] > now
        mult = c.get('revenue_multiplier', 1.0) * (2.0 if boost_active else 1.0)
        rev = daily_rev * days * mult
        total_revenue += rev
        await db.user_companies.update_one(
            {"id": c['id']},
            {"$set": {"last_collection": now}, "$inc": {"total_collected": rev}}
        )
        details.append({"name": c['name'], "revenue": round(rev, 2), "days": round(days, 2)})
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
            "message": f"Receitas coletadas: R$ {total_revenue:,.2f}",
            "total_revenue": round(total_revenue, 2),
            "xp_gained": xp_gain,
            "details": details,
            "new_balance": round(new_money, 2),
        }
    return {"message": "Nenhuma receita para coletar ainda", "total_revenue": 0, "details": []}

@api_router.post("/companies/ad-boost")
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

@api_router.post("/companies/merge")
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
            "monthly_revenue": merged_revenue,
            "employees": merged_employees,
            "level": new_level,
            "revenue_multiplier": c1.get('revenue_multiplier', 1.0) + 0.2,
            "description": f"Resultado da fusão de {c1['name']} e {c2['name']}. Nível {new_level}.",
        }}
    )
    await db.user_companies.delete_one({"id": c2['id']})
    return {
        "message": f"Fusão concluída! {merged_name} criada com +30% de receita!",
        "new_company": {"name": merged_name, "monthly_revenue": merged_revenue, "level": new_level},
    }

# ==================== ASSETS / PATRIMÔNIO SYSTEM ====================

ASSETS_FOR_SALE = [
    # Veículos
    {"name": "Moto CG 160", "category": "veiculo", "subcategory": "Motos", "price": 15000, "description": "Moto econômica para o dia a dia", "appreciation": -0.05, "status_boost": 5, "level_required": 1, "icon": "bicycle"},
    {"name": "Fiat Uno", "category": "veiculo", "subcategory": "Carros", "price": 35000, "description": "Carro popular e econômico", "appreciation": -0.08, "status_boost": 10, "level_required": 1, "icon": "car"},
    {"name": "Toyota Corolla", "category": "veiculo", "subcategory": "Carros", "price": 120000, "description": "Sedan executivo confortável", "appreciation": -0.06, "status_boost": 25, "level_required": 3, "icon": "car"},
    {"name": "BMW X5", "category": "veiculo", "subcategory": "SUVs", "price": 450000, "description": "SUV premium de luxo", "appreciation": -0.04, "status_boost": 50, "level_required": 6, "icon": "car-sport"},
    {"name": "Porsche 911", "category": "veiculo", "subcategory": "Esportivos", "price": 900000, "description": "Esportivo icônico alemão", "appreciation": 0.02, "status_boost": 80, "level_required": 10, "icon": "car-sport"},
    {"name": "Ferrari F8 Tributo", "category": "veiculo", "subcategory": "Esportivos", "price": 3500000, "description": "Superesportivo italiano", "appreciation": 0.05, "status_boost": 150, "level_required": 15, "icon": "car-sport"},
    {"name": "Lancha 32 pés", "category": "veiculo", "subcategory": "Náuticos", "price": 600000, "description": "Lancha para passeios no litoral", "appreciation": -0.03, "status_boost": 60, "level_required": 8, "icon": "boat"},
    {"name": "Iate de Luxo", "category": "veiculo", "subcategory": "Náuticos", "price": 5000000, "description": "Iate com 3 cabines e jacuzzi", "appreciation": 0.01, "status_boost": 200, "level_required": 18, "icon": "boat"},
    {"name": "Helicóptero Robinson R44", "category": "veiculo", "subcategory": "Aéreos", "price": 2500000, "description": "Helicóptero para deslocamento urbano", "appreciation": -0.02, "status_boost": 120, "level_required": 12, "icon": "airplane"},
    {"name": "Jato Executivo Phenom 300", "category": "veiculo", "subcategory": "Aéreos", "price": 25000000, "description": "Jato particular para viagens internacionais", "appreciation": 0.01, "status_boost": 500, "level_required": 20, "icon": "airplane"},
    # Imóveis
    {"name": "Kitnet Centro", "category": "imovel", "subcategory": "Apartamentos", "price": 80000, "description": "Kitnet de 25m² no centro da cidade", "appreciation": 0.03, "status_boost": 15, "level_required": 1, "icon": "home"},
    {"name": "Apartamento 2 Quartos", "category": "imovel", "subcategory": "Apartamentos", "price": 250000, "description": "Apartamento de 65m² em bairro residencial", "appreciation": 0.04, "status_boost": 30, "level_required": 3, "icon": "home"},
    {"name": "Casa 3 Quartos", "category": "imovel", "subcategory": "Casas", "price": 450000, "description": "Casa com quintal em condomínio fechado", "appreciation": 0.05, "status_boost": 50, "level_required": 5, "icon": "home"},
    {"name": "Cobertura Duplex", "category": "imovel", "subcategory": "Apartamentos", "price": 1200000, "description": "Cobertura de 180m² com terraço e piscina", "appreciation": 0.06, "status_boost": 100, "level_required": 8, "icon": "home"},
    {"name": "Mansão Alphaville", "category": "imovel", "subcategory": "Casas", "price": 5000000, "description": "Mansão de 500m² com 6 suítes e piscina", "appreciation": 0.07, "status_boost": 250, "level_required": 15, "icon": "home"},
    {"name": "Penthouse Faria Lima", "category": "imovel", "subcategory": "Apartamentos", "price": 12000000, "description": "Penthouse de 400m² na Faria Lima, SP", "appreciation": 0.08, "status_boost": 400, "level_required": 20, "icon": "home"},
    {"name": "Ilha Privada", "category": "imovel", "subcategory": "Especiais", "price": 50000000, "description": "Ilha particular com infraestrutura completa", "appreciation": 0.10, "status_boost": 1000, "level_required": 25, "icon": "globe"},
    # Luxo
    {"name": "Relógio Rolex Submariner", "category": "luxo", "subcategory": "Relógios", "price": 80000, "description": "Relógio suíço icônico de mergulho", "appreciation": 0.08, "status_boost": 20, "level_required": 5, "icon": "watch"},
    {"name": "Relógio Patek Philippe", "category": "luxo", "subcategory": "Relógios", "price": 500000, "description": "Alta relojoaria suíça, peça de colecionador", "appreciation": 0.12, "status_boost": 80, "level_required": 12, "icon": "watch"},
    {"name": "Bolsa Hermès Birkin", "category": "luxo", "subcategory": "Acessórios", "price": 120000, "description": "Bolsa de luxo mais desejada do mundo", "appreciation": 0.15, "status_boost": 35, "level_required": 8, "icon": "bag"},
    {"name": "Coleção de Arte", "category": "luxo", "subcategory": "Arte", "price": 2000000, "description": "Coleção de pinturas de artistas brasileiros", "appreciation": 0.10, "status_boost": 150, "level_required": 15, "icon": "color-palette"},
    {"name": "Diamante 5 Quilates", "category": "luxo", "subcategory": "Joias", "price": 800000, "description": "Diamante lapidado com certificação GIA", "appreciation": 0.06, "status_boost": 100, "level_required": 10, "icon": "diamond"},
]

async def seed_assets_for_sale():
    count = await db.assets_store.count_documents({})
    if count == 0:
        assets = []
        for seed in ASSETS_FOR_SALE:
            asset = {"id": str(uuid.uuid4()), **seed, "created_at": datetime.utcnow()}
            assets.append(asset)
        await db.assets_store.insert_many(assets)
        logger.info(f"Seeded {len(assets)} assets for sale")

@app.on_event("startup")
async def startup_assets():
    await seed_assets_for_sale()

@api_router.get("/assets/store")
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

@api_router.post("/assets/buy")
async def buy_asset_item(request: dict, current_user: dict = Depends(get_current_user)):
    asset_id = request.get('asset_id')
    asset = await db.assets_store.find_one({"id": asset_id})
    if not asset:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    user = await db.users.find_one({"id": current_user['id']})
    if user['money'] < asset['price']:
        raise HTTPException(status_code=400, detail=f"Saldo insuficiente. Necessário: R$ {asset['price']:,.2f}")
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

@api_router.get("/assets/owned")
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

@api_router.post("/assets/sell")
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
        "message": f"{asset['name']} vendido por R$ {sell_value:,.2f}!",
        "sell_value": sell_value,
        "profit": round(profit, 2),
        "new_balance": round(new_money, 2),
    }

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
        "total_net_worth": round(total, 2),
        "num_companies": len(companies),
        "num_assets": len(assets),
        "num_investments": len(holdings),
    }


@api_router.get("/rankings")
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
            {"position": 3, "icon": "cash", "color": "#CD7F32", "description": "+R$ 25.000", "type": "money"},
        ],
    }


WEEKLY_PRIZES = {
    1: {"type": "xp", "value": 50000, "description": "+50.000 XP de experiência"},
    2: {"type": "boost", "multiplier": 5.0, "duration_hours": 24, "description": "Boost 5x nos ganhos por 24 horas"},
    3: {"type": "money", "value": 25000, "description": "+R$ 25.000 em dinheiro do jogo"},
}


@api_router.post("/rankings/distribute-rewards")
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


@api_router.post("/rankings/claim-reward")
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
        messages.append(f"+R$ {money_amount:,.0f} adicionados à sua conta!")

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

@api_router.get("/rewards/prize-pool")
async def get_prize_pool(current_user: dict = Depends(get_current_user)):
    """Get current monthly prize pool and distribution info"""
    now = datetime.utcnow()
    current_month = now.strftime("%Y-%m")
    
    # Simulated ad revenue (in production, this comes from real ad network)
    # Base: R$ 5000/month simulated ad revenue, 5% goes to prize pool
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
    
    # Check if user has PIX key configured
    user_doc = await db.users.find_one({"id": current_user['id']})
    has_pix = bool(user_doc.get('pix_key'))
    
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
        "has_pix_key": has_pix,
        "pix_key": user_doc.get('pix_key', ''),
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


@api_router.post("/rewards/update-pix")
async def update_pix_key(request: dict, current_user: dict = Depends(get_current_user)):
    """Update user's PIX key for receiving real money rewards"""
    pix_key = request.get('pix_key', '').strip()
    pix_type = request.get('pix_type', 'cpf')  # cpf, email, phone, random
    
    if not pix_key:
        raise HTTPException(status_code=400, detail="Chave PIX não pode estar vazia")
    
    await db.users.update_one({"id": current_user['id']}, {
        "$set": {
            "pix_key": pix_key,
            "pix_type": pix_type,
            "pix_updated_at": datetime.utcnow(),
        }
    })
    
    return {"success": True, "message": f"Chave PIX atualizada: {pix_key}"}


@api_router.post("/rewards/distribute-monthly")
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
    
    return {"success": True, "message": f"Premiação de {current_month} distribuída! Pool: R$ {prize_pool_total:.2f}"}


@api_router.post("/rewards/claim-real")
async def claim_real_money_reward(request: dict, current_user: dict = Depends(get_current_user)):
    """Claim a real money reward (requires PIX key)"""
    reward_id = request.get('reward_id')
    
    # Check PIX key
    user = await db.users.find_one({"id": current_user['id']})
    if not user.get('pix_key'):
        raise HTTPException(status_code=400, detail="Configure sua chave PIX no perfil antes de resgatar!")
    
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
            "pix_key_used": user.get('pix_key'),
            "status": "processing",  # In production: pending -> processing -> paid
        }
    })
    
    return {
        "success": True,
        "message": f"Resgate de R$ {reward['amount']:.2f} solicitado!\n\nPagamento será enviado para sua chave PIX: {user['pix_key']}\n\nPrazo: até 5 dias úteis.",
        "amount": reward['amount'],
        "position": reward['position'],
    }


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
    # Earnings Boosts (time-limited multipliers)
    {"id": "earnings_2x_1h", "category": "ganhos", "name": "Boost 2x (1 hora)", "description": "Dobre todos os seus ganhos por 1 hora", "game_reward": {"earnings_multiplier": 2.0, "duration_hours": 1}, "price_brl": 1.90, "icon": "flash", "color": "#E91E63", "popular": False},
    {"id": "earnings_3x_3h", "category": "ganhos", "name": "Boost 3x (3 horas)", "description": "Triplique todos os seus ganhos por 3 horas", "game_reward": {"earnings_multiplier": 3.0, "duration_hours": 3}, "price_brl": 4.90, "icon": "flash", "color": "#E91E63", "popular": True},
    {"id": "earnings_5x_6h", "category": "ganhos", "name": "Boost 5x (6 horas)", "description": "Quintuplique seus ganhos por 6 horas inteiras!", "game_reward": {"earnings_multiplier": 5.0, "duration_hours": 6}, "price_brl": 9.90, "icon": "flash", "color": "#E91E63", "popular": False, "best_value": True},
    {"id": "earnings_10x_12h", "category": "ganhos", "name": "Boost 10x (12 horas)", "description": "O boost MÁXIMO! 10x ganhos por 12 horas", "game_reward": {"earnings_multiplier": 10.0, "duration_hours": 12}, "price_brl": 19.90, "icon": "rocket", "color": "#E91E63", "popular": False},
]

@api_router.get("/store/items")
async def get_store_items(category: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    """Get all items available in the game store"""
    items = STORE_ITEMS
    if category:
        items = [i for i in items if i['category'] == category]
    return items

@api_router.post("/store/purchase")
async def purchase_store_item(request: dict, current_user: dict = Depends(get_current_user)):
    """Purchase a store item (MOCK payment - real payment integration pending)"""
    item_id = request.get('item_id')
    payment_method = request.get('payment_method', 'credit_card')  # credit_card, pix

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
        messages.append(f"+R$ {reward['money']:,.0f} adicionados à sua conta!")

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

@api_router.get("/store/purchases")
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

# ==================== DAILY FREE MONEY (PROPAGANDA DIÁRIA) ====================

@api_router.post("/store/daily-reward")
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
        "message": f"Propaganda assistida! Você ganhou R$ {reward_amount:,.0f}!",
        "amount": reward_amount,
        "new_balance": round(new_money, 2),
        "level_bonus": user_level * 100,
    }

@api_router.get("/store/daily-reward-status")
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
    }


# ==================== FRANCHISE SYSTEM (FRANQUIAS) ====================

FRANCHISE_SEGMENTS = ['restaurante', 'loja', 'fabrica']

@api_router.post("/companies/create-franchise")
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
        raise HTTPException(status_code=400, detail=f"Saldo insuficiente. Custo da franquia: R$ {franchise_cost:,.0f}")
    
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
        "monthly_revenue": franchise_revenue,
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
        "monthly_revenue": franchise_revenue,
        "new_balance": round(new_money, 2),
    }


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

@api_router.get("/market/events")
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

@api_router.post("/market/trigger-event")
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
    import random
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

@api_router.get("/assets/images/{asset_key}")
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


# ==================== BANCO ONLINE ====================

# --- Credit Card ---
@api_router.get("/bank/account")
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


@api_router.post("/bank/credit-card/purchase")
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
        raise HTTPException(status_code=400, detail=f"Limite insuficiente. Disponível: R$ {available:,.2f}")
    
    # 1 mile per R$ 1 spent
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
        "message": f"Compra de R$ {amount:,.2f} realizada! +{miles_earned} milhas",
        "miles_earned": miles_earned,
        "total_miles": card.get('miles_points', 0) + miles_earned,
        "balance_used": card.get('balance_used', 0) + amount,
    }


@api_router.post("/bank/credit-card/pay-bill")
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
        "message": f"Fatura de R$ {amount:,.2f} paga com sucesso!",
        "new_balance": round(user['money'] - amount, 2),
        "remaining_bill": round(balance_used - amount, 2),
    }


@api_router.post("/bank/credit-card/redeem-miles")
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
@api_router.post("/bank/loan/apply")
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
            raise HTTPException(status_code=400, detail=f"Valor máximo sem garantia: R$ {max_amount:,.0f}")
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
            raise HTTPException(status_code=400, detail=f"Valor máximo com esta garantia: R$ {max_amount:,.0f}")
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
        "message": f"Empréstimo de R$ {amount:,.0f} aprovado! Parcela: R$ {monthly_payment:,.2f}/mês",
        "loan_id": loan['id'],
        "monthly_payment": monthly_payment,
        "total_with_interest": round(total_with_interest, 2),
        "months": months,
        "new_balance": round(new_money, 2),
    }


@api_router.post("/bank/loan/pay")
async def pay_loan_installment(request: dict, current_user: dict = Depends(get_current_user)):
    """Make a monthly loan payment"""
    loan_id = request.get('loan_id')
    
    loan = await db.loans.find_one({"id": loan_id, "user_id": current_user['id'], "status": "active"})
    if not loan:
        raise HTTPException(status_code=404, detail="Empréstimo não encontrado")
    
    payment = loan['monthly_payment']
    user = await db.users.find_one({"id": current_user['id']})
    if user['money'] < payment:
        raise HTTPException(status_code=400, detail=f"Saldo insuficiente. Parcela: R$ {payment:,.2f}")
    
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
    
    msg = f"Parcela {new_payments}/{loan['months']} paga! R$ {payment:,.2f}"
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


@api_router.post("/bank/loan/payoff")
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
        raise HTTPException(status_code=400, detail=f"Saldo insuficiente. Valor de quitação: R$ {payoff_amount:,.2f}")
    
    await db.loans.update_one({"_id": loan['_id']}, {"$set": {
        "remaining_balance": 0,
        "status": "paid_off",
    }})
    await db.users.update_one({"id": current_user['id']}, {"$inc": {"money": -payoff_amount}})
    
    return {
        "success": True,
        "message": f"Empréstimo quitado com desconto! Economia: R$ {savings:,.2f}",
        "payoff_amount": round(payoff_amount, 2),
        "savings": round(savings, 2),
        "new_balance": round(user['money'] - payoff_amount, 2),
    }


# ==================== EMPRESAS - SELL & FRANCHISE IMPROVEMENTS ====================

@api_router.post("/companies/sell")
async def sell_company(request: dict, current_user: dict = Depends(get_current_user)):
    """Sell an owned company"""
    company_id = request.get('company_id')
    
    company = await db.user_companies.find_one({"id": company_id, "user_id": current_user['id']})
    if not company:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    
    # Sell price: 80% of purchase price + collected revenue bonus
    sell_price = round(company.get('purchase_price', 0) * 0.8)
    
    # Also delete all franchises of this company
    if not company.get('is_franchise'):
        franchise_count = await db.user_companies.count_documents({"parent_company_id": company_id, "user_id": current_user['id']})
        if franchise_count > 0:
            await db.user_companies.delete_many({"parent_company_id": company_id, "user_id": current_user['id']})
    
    await db.user_companies.delete_one({"_id": company['_id']})
    
    user = await db.users.find_one({"id": current_user['id']})
    new_money = user['money'] + sell_price
    await db.users.update_one({"id": current_user['id']}, {"$set": {"money": new_money}})
    
    return {
        "success": True,
        "message": f"Empresa '{company.get('name')}' vendida por R$ {sell_price:,.0f}!",
        "sell_price": sell_price,
        "new_balance": round(new_money, 2),
    }


# ==================== COMPANY PURCHASE OFFERS ====================

import random as _random

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


@api_router.get("/companies/offers")
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
        if company['id'] in companies_with_recent_offer:
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
            "company_id": company['id'],
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


@api_router.post("/companies/offers/respond")
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
    profit_text = f"Lucro: R$ {profit:,.0f}" if profit >= 0 else f"Prejuízo: R$ {abs(profit):,.0f}"

    return {
        "success": True,
        "message": f"Empresa '{company.get('name')}' vendida para {offer.get('buyer_name')} por R$ {offer_amount:,.0f}!\n\n{profit_text}\nXP Bônus: +{xp_bonus:,}",
        "offer_amount": offer_amount,
        "profit": profit,
        "xp_bonus": xp_bonus,
        "new_balance": round(new_money, 2),
    }


# ==================== AI COACHING ====================

COACHING_SYSTEM_PROMPT = """Você é o Coach Virtual de Negócios do jogo Business Empire: RichMan. 
Você é um mentor experiente, motivador e direto. Fale em português do Brasil.
Analise os dados do jogador e dê conselhos estratégicos personalizados.
Seja breve (max 3-4 parágrafos), use emojis ocasionalmente, e sempre termine com uma dica acionável.
Você pode sugerir: investir em ações/cripto, comprar empresas, fazer cursos, usar o banco, comprar imóveis.
Adapte o tom ao nível do jogador: iniciante (nível 1-10), intermediário (10-30), avançado (30+)."""

@api_router.post("/coaching/advice")
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


@api_router.get("/coaching/history")
async def get_coaching_history(current_user: dict = Depends(get_current_user)):
    """Get coaching conversation history"""
    history = await db.coaching_history.find(
        {"user_id": current_user['id']}
    ).sort("created_at", -1).to_list(20)
    for h in history:
        h.pop('_id', None)
        h['created_at'] = h['created_at'].isoformat() if isinstance(h.get('created_at'), datetime) else str(h.get('created_at', ''))
    return {"history": history}


# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
