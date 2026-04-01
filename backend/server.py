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
        start = exp['start_date']
        end = exp.get('end_date', datetime.utcnow())
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
        start = exp['start_date']
        end = exp.get('end_date', datetime.utcnow())
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
    
    if days_elapsed < 0.1:  # Less than ~2.4 hours
        return {
            "message": "Você já coletou seus ganhos recentemente. Volte mais tarde!",
            "earnings": 0,
            "days_elapsed": 0
        }
    
    # Calculate earnings (can accumulate multiple days)
    daily_salary = current_job['salary'] / 30
    total_earnings = daily_salary * days_elapsed
    
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
        "earnings": total_earnings,
        "xp_gained": xp_gain,
        "new_level": new_level,
        "new_money": new_money,
        "days_elapsed": days_elapsed,
        "days_worked": new_days_worked,
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
        app['job'] = job
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
    current_job['job_details'] = job
    del current_job['_id']
    
    return current_job

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
