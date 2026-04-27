"""BizRealms - Shared utility functions."""
import bcrypt
import jwt
from datetime import datetime, timedelta
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from config import JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRATION_DAYS
from database import db

security = HTTPBearer()

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_token(user_id: str) -> str:
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(days=JWT_EXPIRATION_DAYS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    token = credentials.credentials
    payload = decode_token(token)
    user_id = payload.get('user_id')
    user = await db.users.find_one({'id': user_id})
    if not user:
        raise HTTPException(status_code=401, detail="Usuário não encontrado")
    return user

def calculate_level(experience_points: int) -> int:
    """Calculate level from XP. Progressive curve - each level needs more XP.
    Level 1: 0 XP, Level 2: 5000 XP, Level 3: 12000 XP, Level 4: 21000 XP, etc.
    Formula: XP needed for level N = 5000 + (N-2) * 2000 (cumulative)
    """
    if experience_points < 5000:
        return 1
    xp = experience_points
    level = 1
    threshold = 5000  # XP to reach level 2
    increment = 2000  # Each subsequent level needs 2000 more XP
    while xp >= threshold:
        xp -= threshold
        level += 1
        threshold += increment
    return level
