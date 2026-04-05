"""BizRealms - All Pydantic models."""
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
import uuid
from datetime import datetime


class Education(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    degree: str
    field: str
    institution: str
    year_completed: int
    level: int

class Certification(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    issuer: str
    date_obtained: datetime
    skill_boost: int

class WorkExperience(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    company: str
    position: str
    start_date: datetime
    end_date: Optional[datetime] = None
    is_current: bool = False
    salary: float
    experience_gained: int

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    password_hash: str = ""
    name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    email_verified: bool = False
    auth_provider: str = "email"
    auth_provider_id: Optional[str] = None
    onboarding_completed: bool = False
    avatar_color: str = "green"
    avatar_icon: str = "person"
    avatar_photo: Optional[str] = None
    background: str = ""
    dream: str = ""
    personality: dict = Field(default_factory=lambda: {"ambição": 5, "risco": 5, "social": 5, "analítico": 5})
    money: float = 1000.0
    experience_points: int = 0
    level: int = 1
    location: str = "São Paulo, Brazil"
    education: List[Education] = []
    certifications: List[Certification] = []
    work_experience: List[WorkExperience] = []
    skills: dict = Field(default_factory=lambda: {"liderança": 1, "comunicação": 1, "técnico": 1, "financeiro": 1, "negociação": 1})

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
    paypal_email: Optional[str] = None
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
    avatar_photo: Optional[str] = None
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
    requirements: dict = Field(default_factory=lambda: {"education_level": 1, "experience_months": 0, "skills": {}})
    status: str = "open"
    created_at: datetime = Field(default_factory=datetime.utcnow)

class JobApplication(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    job_id: str
    status: str = "pending"
    match_score: float = 0.0
    applied_at: datetime = Field(default_factory=datetime.utcnow)

class Course(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    duration_hours: int
    cost: float
    skill_boost: dict = Field(default_factory=dict)
    education_level_boost: int = 0
    category: str = "professional"

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
    hours: int = 8

class AdBoost(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    multiplier: float = 1.0
    ads_watched: int = 0
    expires_at: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)

class UserCourseComplete(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    course_id: str
    course_name: str
    completed_at: datetime = Field(default_factory=datetime.utcnow)
    earnings_boost: float

class SocialAuthRequest(BaseModel):
    provider: str
    token: str
    name: Optional[str] = None
    email: Optional[str] = None
