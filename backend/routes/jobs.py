"""BizRealms - Jobs Routes."""
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
            "title": "Auxiliar de Produção",
            "company": "Fábrica Nacional",
            "description": "Auxiliar nas atividades de produção e organização do setor",
            "salary": 1500.0,
            "location": "São Paulo, Brazil",
            "requirements": {"education_level": 0, "experience_months": 0, "skills": {}},
            "status": "open",
            "min_level": 0,
            "created_at": datetime.utcnow()
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Estagiário",
            "company": "StartUp Hub",
            "description": "Apoio em diversas áreas da empresa",
            "salary": 1200.0,
            "location": "São Paulo, Brazil",
            "requirements": {"education_level": 0, "experience_months": 0, "skills": {}},
            "status": "open",
            "min_level": 0,
            "created_at": datetime.utcnow()
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Vendedor",
            "company": "ComercioMax",
            "description": "Vendas diretas e atendimento ao cliente",
            "salary": 2000.0,
            "location": "Rio de Janeiro, Brazil",
            "requirements": {"education_level": 1, "experience_months": 0, "skills": {"comunicação": 2}},
            "status": "open",
            "created_at": datetime.utcnow()
        },
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
            "title": "Gerente de Projetos",
            "company": "Corporate Solutions",
            "description": "Gerenciar equipes e projetos estratégicos",
            "salary": 8000.0,
            "location": "São Paulo, Brazil",
            "requirements": {"education_level": 2, "experience_months": 24, "skills": {"liderança": 5, "comunicação": 4}},
            "status": "open",
            "created_at": datetime.utcnow()
        },
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

@router.get("/jobs/available-for-level")
async def get_jobs_for_level(current_user: dict = Depends(get_current_user)):
    """Get jobs including higher-level ones based on user level"""
    user = await db.users.find_one({"id": current_user['id']})
    user_level = user.get('level', 1)
    
    # Seed jobs if empty
    job_count = await db.jobs.count_documents({})
    if job_count == 0:
        await seed_jobs()
    
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


@router.post("/jobs/apply")
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
    else:
        # No education requirement = automatic match
        max_score += 30
        score += 30
    
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
    else:
        # No experience requirement = automatic match
        max_score += 20
        score += 20
    
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
    else:
        # No skills requirement = automatic match
        max_score += 50
        score += 50
    
    # If no requirements, 100% match
    if max_score == 0:
        return 100.0
    
    return (score / max_score) * 100

@router.post("/jobs/accept")
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

@router.get("/jobs/collect-earnings")
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
    
    # Game time: 30 game days = 72 real hours (3 real days) => 1 game day = 8640 real seconds
    # This means a full monthly salary takes ~3 real days to accumulate
    GAME_DAY_SECONDS = 8640
    MAX_COLLECTIBLE_DAYS = 30  # Cap: max 1 game month of accumulated earnings
    MIN_COLLECTION_INTERVAL = 1800  # Minimum 30 minutes between collections
    now = datetime.utcnow()
    
    real_seconds_elapsed = (now - last_collection).total_seconds()
    
    if real_seconds_elapsed < MIN_COLLECTION_INTERVAL:
        minutes_left = int((MIN_COLLECTION_INTERVAL - real_seconds_elapsed) / 60)
        return {
            "message": f"Aguarde {minutes_left} minuto(s) para coletar novamente.",
            "earnings": 0,
            "days_elapsed": 0
        }
    
    game_days_elapsed = min(real_seconds_elapsed / GAME_DAY_SECONDS, MAX_COLLECTIBLE_DAYS)
    
    # Calculate earnings based on game days (salary is per 30 game days)
    daily_salary = current_job['salary'] / 30
    total_earnings = daily_salary * game_days_elapsed
    
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
    xp_gain = int(80 * game_days_elapsed)
    
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
    new_days_worked = current_job.get('days_worked', 0) + int(game_days_elapsed)
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
    career_opportunity = None
    if new_days_worked % 30 == 0 and new_days_worked > current_job.get('days_worked', 0):
        new_salary = round(current_job['salary'] * 1.10, 2)
        await db.work_experiences.update_one(
            {'_id': current_job['_id']},
            {'$set': {'salary': new_salary, 'promotions': current_job.get('promotions', 0) + 1}}
        )
        promotion_message = f"Promoção! Seu salário aumentou para $ {new_salary:.2f}/mês!"
    
    # Career progression: check courses & experience for new opportunities
    user_courses = await db.user_courses.find({"user_id": current_user['id'], "completed": True}).to_list(50)
    total_courses = len(user_courses)
    total_exp_months = new_days_worked // 30
    
    # Generate career opportunity based on progression
    CAREER_PATHS = [
        {"trigger_courses": 1, "trigger_months": 2, "title": "Operador de Produção", "salary_mult": 1.4, "company": current_job.get('company', 'Empresa'), "desc": "Promoção interna para operador!"},
        {"trigger_courses": 2, "trigger_months": 3, "title": "Supervisor de Equipe", "salary_mult": 1.8, "company": current_job.get('company', 'Empresa'), "desc": "Você foi promovido a supervisor!"},
        {"trigger_courses": 3, "trigger_months": 5, "title": "Coordenador de Área", "salary_mult": 2.3, "company": current_job.get('company', 'Empresa'), "desc": "Nova posição: Coordenador!"},
        {"trigger_courses": 4, "trigger_months": 8, "title": "Gerente de Departamento", "salary_mult": 3.0, "company": current_job.get('company', 'Empresa'), "desc": "Promoção a Gerente!"},
        {"trigger_courses": 6, "trigger_months": 12, "title": "Diretor Executivo", "salary_mult": 4.0, "company": current_job.get('company', 'Empresa'), "desc": "Você chegou à Diretoria!"},
    ]
    
    current_promotions = current_job.get('career_level', 0)
    for i, path in enumerate(CAREER_PATHS):
        if i <= current_promotions:
            continue
        if total_courses >= path['trigger_courses'] and total_exp_months >= path['trigger_months']:
            # Offer this career opportunity
            base_salary = current_job.get('original_salary', current_job['salary'])
            new_opp_salary = round(base_salary * path['salary_mult'], 2)
            career_opportunity = {
                "level": i,
                "title": path['title'],
                "company": path['company'],
                "description": path['desc'],
                "new_salary": new_opp_salary,
                "salary_increase": round(new_opp_salary - current_job['salary'], 2),
                "required_courses": path['trigger_courses'],
                "required_months": path['trigger_months'],
            }
            break
    
    # Also check if external offers are available (headhunter)
    headhunter_offer = None
    if total_courses >= 2 and total_exp_months >= 4 and random.random() < 0.3:
        offer_titles = [
            ("Analista Sênior", "Consultoria Global", 1.5),
            ("Especialista de Mercado", "FinTech Solutions", 1.6),
            ("Líder de Inovação", "StartUp Ventures", 1.7),
            ("Head de Operações", "Grupo Industrial", 2.0),
            ("Diretor Comercial", "MegaCorp", 2.5),
        ]
        offer = random.choice(offer_titles)
        headhunter_salary = round(current_job['salary'] * offer[2], 2)
        headhunter_offer = {
            "title": offer[0],
            "company": offer[1],
            "salary": headhunter_salary,
            "salary_increase": round(headhunter_salary - current_job['salary'], 2),
        }
    
    return {
        "message": f"Você coletou seus ganhos de {game_days_elapsed:.1f} dias de trabalho!",
        "earnings": round(total_earnings, 2),
        "xp_gained": xp_gain,
        "new_level": new_level,
        "new_money": round(new_money, 2),
        "days_elapsed": round(game_days_elapsed, 2),
        "days_worked": new_days_worked,
        "boost_multiplier": boost_multiplier,
        "courses_boost": round(courses_boost, 2),
        "promotion": promotion_message,
        "career_opportunity": career_opportunity,
        "headhunter_offer": headhunter_offer,
    }

@router.post("/jobs/accept-career-opportunity")
async def accept_career_opportunity(request: dict, current_user: dict = Depends(get_current_user)):
    """Accept an internal career opportunity (promotion within company)."""
    level = request.get('level', 0)
    new_title = request.get('title', '')
    new_salary = request.get('new_salary', 0)
    
    current_job = await db.work_experiences.find_one({
        "user_id": current_user['id'],
        "is_current": True
    })
    if not current_job:
        raise HTTPException(status_code=400, detail="Você não está empregado.")
    
    old_title = current_job.get('job_title', current_job.get('title', ''))
    old_salary = current_job['salary']
    
    await db.work_experiences.update_one(
        {'_id': current_job['_id']},
        {'$set': {
            'job_title': new_title,
            'title': new_title,
            'salary': new_salary,
            'original_salary': current_job.get('original_salary', old_salary),
            'career_level': level,
            'promoted_at': datetime.utcnow(),
        }}
    )
    
    # Notification
    await db.notifications.insert_one({
        "id": str(uuid.uuid4()),
        "user_id": current_user['id'],
        "type": "career",
        "title": f"Promoção: {new_title}!",
        "message": f"Parabéns! Você foi promovido de {old_title} para {new_title}. Novo salário: $ {new_salary:,.2f}/mês",
        "read": False,
        "created_at": datetime.utcnow(),
    })
    
    return {
        "success": True,
        "message": f"Parabéns pela promoção! Você agora é {new_title} com salário de $ {new_salary:,.2f}/mês!",
        "old_title": old_title,
        "new_title": new_title,
        "old_salary": old_salary,
        "new_salary": new_salary,
    }


@router.post("/jobs/accept-headhunter")
async def accept_headhunter_offer(request: dict, current_user: dict = Depends(get_current_user)):
    """Accept a headhunter offer (switch to new company)."""
    new_title = request.get('title', '')
    new_company = request.get('company', '')
    new_salary = request.get('salary', 0)
    
    current_job = await db.work_experiences.find_one({
        "user_id": current_user['id'],
        "is_current": True
    })
    if not current_job:
        raise HTTPException(status_code=400, detail="Você não está empregado.")
    
    old_company = current_job.get('company', '')
    old_title = current_job.get('job_title', current_job.get('title', ''))
    
    # End current job
    await db.work_experiences.update_one(
        {'_id': current_job['_id']},
        {'$set': {'is_current': False, 'end_date': datetime.utcnow()}}
    )
    
    # Create new job
    await db.work_experiences.insert_one({
        "id": str(uuid.uuid4()),
        "user_id": current_user['id'],
        "job_id": f"headhunter_{uuid.uuid4().hex[:8]}",
        "job_title": new_title,
        "title": new_title,
        "company": new_company,
        "salary": new_salary,
        "original_salary": new_salary,
        "start_date": datetime.utcnow(),
        "last_collection_date": datetime.utcnow(),
        "is_current": True,
        "days_worked": 0,
        "career_level": 0,
        "promotions": 0,
        "source": "headhunter",
    })
    
    # Notification
    await db.notifications.insert_one({
        "id": str(uuid.uuid4()),
        "user_id": current_user['id'],
        "type": "career",
        "title": f"Novo emprego: {new_title}!",
        "message": f"Você saiu de {old_company} e agora trabalha como {new_title} na {new_company}. Salário: $ {new_salary:,.2f}/mês",
        "read": False,
        "created_at": datetime.utcnow(),
    })
    
    return {
        "success": True,
        "message": f"Parabéns! Você agora é {new_title} na {new_company}. Salário: $ {new_salary:,.2f}/mês!",
        "old_company": old_company,
        "new_company": new_company,
        "new_title": new_title,
        "new_salary": new_salary,
    }


@router.post("/jobs/resign")
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
@router.post("/ads/watch")
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

@router.get("/ads/current-boost")
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

@router.get("/jobs/my-applications")
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

@router.get("/jobs/current")
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
@router.get("/courses")
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

@router.post("/courses/enroll")
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

@router.get("/courses/my-courses")
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

