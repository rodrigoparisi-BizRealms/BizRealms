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
    onboarding_completed: bool
    avatar_color: str
    avatar_icon: str
    avatar_photo: Optional[str] = None
    background: str
    dream: str
    personality: dict
    money: float
    experience_points: int
    level: int
    location: str
    education: List[Education]
    certifications: List[Certification]
    work_experience: List[WorkExperience]
    skills: dict
    created_at: datetime

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
            # Still active, increase multiplier
            new_multiplier = min(10.0, ad_boost.get('multiplier', 1.0) + 1.0)
            new_ads_watched = ad_boost.get('ads_watched', 0) + 1
            # Add 60 seconds per ad
            new_expires_at = expires_at + timedelta(seconds=60)
        else:
            # Expired, reset
            new_multiplier = 2.0
            new_ads_watched = 1
            new_expires_at = now + timedelta(seconds=60)
        
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
        # Create new boost
        new_multiplier = 2.0
        new_ads_watched = 1
        new_expires_at = now + timedelta(seconds=60)
        
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
    
    return {
        "message": f"Propaganda assistida! Seus ganhos aumentaram {new_multiplier}x!",
        "multiplier": new_multiplier,
        "ads_watched": new_ads_watched,
        "expires_at": new_expires_at.isoformat(),
        "seconds_remaining": 60 * new_ads_watched if new_ads_watched <= 10 else 600,
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
    
    seconds_remaining = (expires_at - now).total_seconds()
    
    # Calculate current multiplier based on decay
    # Loses 1x every 60 seconds
    time_passed = (now - ad_boost.get('created_at', now)).total_seconds()
    decay_amount = int(time_passed / 60)
    current_multiplier = max(1.0, ad_boost.get('multiplier', 1.0) - decay_amount)
    
    return {
        "active": True,
        "multiplier": current_multiplier,
        "max_multiplier": ad_boost.get('multiplier', 1.0),
        "ads_watched": ad_boost.get('ads_watched', 0),
        "seconds_remaining": int(seconds_remaining),
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
    """Get available courses"""
    courses = [
        {
            "id": "excel-avancado",
            "name": "Excel Avançado",
            "description": "Domine planilhas e automação",
            "cost": 500,
            "earnings_boost": 0.10,  # 10% permanent boost
            "skill_boost": {"técnico": 1},
            "duration": "Instantâneo",
            "level_required": 1
        },
        {
            "id": "gestao-projetos",
            "name": "Gestão de Projetos",
            "description": "Aprenda metodologias ágeis e PMI",
            "cost": 1200,
            "earnings_boost": 0.20,  # 20% permanent boost
            "skill_boost": {"liderança": 2},
            "duration": "Instantâneo",
            "level_required": 3
        },
        {
            "id": "ingles-negocios",
            "name": "Inglês para Negócios",
            "description": "Comunicação profissional internacional",
            "cost": 800,
            "earnings_boost": 0.15,  # 15% permanent boost
            "skill_boost": {"comunicação": 2},
            "duration": "Instantâneo",
            "level_required": 2
        },
        {
            "id": "analise-dados",
            "name": "Análise de Dados",
            "description": "Power BI, Python e visualização",
            "cost": 1500,
            "earnings_boost": 0.25,  # 25% permanent boost
            "skill_boost": {"técnico": 2, "financeiro": 1},
            "duration": "Instantâneo",
            "level_required": 5
        },
        {
            "id": "negociacao-vendas",
            "name": "Negociação e Vendas",
            "description": "Técnicas avançadas de fechamento",
            "cost": 600,
            "earnings_boost": 0.12,  # 12% permanent boost
            "skill_boost": {"negociação": 2},
            "duration": "Instantâneo",
            "level_required": 1
        },
        {
            "id": "lideranca-estrategica",
            "name": "Liderança Estratégica",
            "description": "MBA executivo resumido",
            "cost": 3000,
            "earnings_boost": 0.40,  # 40% permanent boost
            "skill_boost": {"liderança": 3, "financeiro": 2},
            "duration": "Instantâneo",
            "level_required": 10
        }
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
    
    # Get course details (in real app, this would be from DB)
    courses_list = [
        {"id": "excel-avancado", "name": "Excel Avançado", "cost": 500, "earnings_boost": 0.10, "skill_boost": {"técnico": 1}},
        {"id": "gestao-projetos", "name": "Gestão de Projetos", "cost": 1200, "earnings_boost": 0.20, "skill_boost": {"liderança": 2}},
        {"id": "ingles-negocios", "name": "Inglês para Negócios", "cost": 800, "earnings_boost": 0.15, "skill_boost": {"comunicação": 2}},
        {"id": "analise-dados", "name": "Análise de Dados", "cost": 1500, "earnings_boost": 0.25, "skill_boost": {"técnico": 2, "financeiro": 1}},
        {"id": "negociacao-vendas", "name": "Negociação e Vendas", "cost": 600, "earnings_boost": 0.12, "skill_boost": {"negociação": 2}},
        {"id": "lideranca-estrategica", "name": "Liderança Estratégica", "cost": 3000, "earnings_boost": 0.40, "skill_boost": {"liderança": 3, "financeiro": 2}}
    ]
    
    course = next((c for c in courses_list if c['id'] == request.course_id), None)
    if not course:
        raise HTTPException(status_code=404, detail="Curso não encontrado")
    
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

def get_current_price(asset: dict) -> float:
    """Get the current simulated price for an asset"""
    history = generate_price_history(asset, 30)
    if history:
        return history[-1]['price']
    return asset['base_price']

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
