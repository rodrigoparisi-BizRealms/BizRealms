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
