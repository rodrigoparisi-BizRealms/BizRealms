"""BizRealms - User Routes."""
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

@router.get("/user/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    """Get current user profile"""
    del current_user['password_hash']
    del current_user['_id']
    return current_user

@router.put("/user/avatar-photo")
async def update_avatar_photo(photo_data: dict, current_user: dict = Depends(get_current_user)):
    """Update user avatar photo"""
    await db.users.update_one(
        {'id': current_user['id']},
        {'$set': {'avatar_photo': photo_data.get('avatar_photo')}}
    )
    return {"message": "Foto atualizada com sucesso"}

@router.put("/user/personal-data")
async def update_personal_data(data: dict, current_user: dict = Depends(get_current_user)):
    """Update user personal data (name, address, phone, etc.)"""
    allowed = ['full_name', 'address', 'city', 'state', 'zip_code', 'phone', 'name', 'email', 'location', 'identity_document', 'country']
    update_data = {k: v for k, v in data.items() if k in allowed and v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="Nenhum dado válido para atualizar")
    await db.users.update_one(
        {'id': current_user['id']},
        {'$set': update_data}
    )
    return {"message": "Dados pessoais atualizados com sucesso", "updated_fields": list(update_data.keys())}

@router.delete("/user/education/{education_id}")
async def delete_education(education_id: str, current_user: dict = Depends(get_current_user)):
    """Delete education entry"""
    await db.users.update_one(
        {'id': current_user['id']},
        {'$pull': {'education': {'id': education_id}}}
    )
    return {"message": "Educação removida com sucesso"}

@router.delete("/user/certification/{cert_id}")
async def delete_certification(cert_id: str, current_user: dict = Depends(get_current_user)):
    """Delete certification entry"""
    await db.users.update_one(
        {'id': current_user['id']},
        {'$pull': {'certifications': {'id': cert_id}}}
    )
    return {"message": "Certificação removida com sucesso"}

@router.put("/user/location")
async def update_location(location: dict, current_user: dict = Depends(get_current_user)):
    """Update user location"""
    await db.users.update_one(
        {'id': current_user['id']},
        {'$set': {'location': location['location']}}
    )
    return {"message": "Localização atualizada com sucesso", "location": location['location']}

# EDUCATION ROUTES
@router.post("/user/education")
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
@router.post("/user/certification")
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

@router.get("/user/stats")
async def get_user_stats(current_user: dict = Depends(get_current_user)):
    """Get user statistics"""
    total_education = len(current_user.get('education', []))
    total_certifications = len(current_user.get('certifications', []))
    total_work_experience = len(set(exp.get('job_title', exp.get('title', '')) for exp in current_user.get('work_experience', [])))
    
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

@router.get("/user/profile/{user_id}")
async def get_public_profile(user_id: str, current_user: dict = Depends(get_current_user)):
    """Get a public player profile for comparison"""
    try:
        target_user = await db.users.find_one({"id": user_id})
    except Exception:
        raise HTTPException(status_code=404, detail="Jogador não encontrado")
    
    if not target_user:
        raise HTTPException(status_code=404, detail="Jogador não encontrado")
    
    # Count companies
    uid = target_user.get("id", str(target_user.get("_id", "")))
    companies = await db.user_companies.count_documents({"user_id": uid})
    # Count assets
    assets = await db.user_assets.count_documents({"user_id": uid})
    # Count investments
    investments = await db.user_investments.count_documents({"user_id": uid})
    
    # Build public profile (no sensitive data)
    return {
        "id": uid,
        "name": target_user.get("name", "Jogador"),
        "avatar_color": target_user.get("avatar_color", "#4CAF50"),
        "level": target_user.get("level", 1),
        "experience_points": target_user.get("experience_points", 0),
        "money": target_user.get("money", 0),
        "companies_count": companies,
        "assets_count": assets,
        "investments_count": investments,
        "background": target_user.get("background", ""),
        "dream": target_user.get("dream", ""),
        "education_count": len(target_user.get("education", [])),
        "certification_count": len(target_user.get("certifications", [])),
        "work_experience_count": len(set(exp.get('job_title', exp.get('title', '')) for exp in target_user.get('work_experience', []))),
        "created_at": target_user.get("created_at", "").isoformat() if hasattr(target_user.get("created_at", ""), 'isoformat') else str(target_user.get("created_at", "")),
        # Comparison with current user
        "comparison": {
            "my_level": current_user.get("level", 1),
            "my_money": current_user.get("money", 0),
        }
    }
@router.get("/character/backgrounds")
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

@router.get("/character/dreams")
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

@router.post("/character/complete-profile")
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


