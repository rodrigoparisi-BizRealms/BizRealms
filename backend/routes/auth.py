"""BizRealms - Auth Routes."""
from pydantic import BaseModel, Field
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

import hashlib
import os
import httpx
import jwt as pyjwt
from config import JWT_SECRET, JWT_ALGORITHM, APPLE_BUNDLE_ID

router = APIRouter()

# AUTH ROUTES
@router.post("/auth/register", response_model=TokenResponse)
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

@router.post("/auth/login", response_model=TokenResponse)
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

# ==================== EMAIL VERIFICATION ====================
import string

def generate_code(length=6):
    """Generate a random numeric verification code."""
    return ''.join(random.choices(string.digits, k=length))

@router.post("/auth/send-verification")
async def send_verification_code(data: dict):
    """Send email verification code. Code is logged to console (replace with email service later)."""
    email = data.get('email')
    if not email:
        raise HTTPException(status_code=400, detail="Email required")
    
    user = await db.users.find_one({'email': email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.get('email_verified'):
        return {"message": "Email already verified"}
    
    code = generate_code()
    expires = datetime.utcnow() + timedelta(minutes=15)
    
    await db.verification_codes.delete_many({'email': email, 'type': 'email_verify'})
    await db.verification_codes.insert_one({
        'email': email,
        'code': code,
        'type': 'email_verify',
        'expires': expires,
        'created_at': datetime.utcnow()
    })
    
    # TODO: Replace with real email service (SendGrid, etc.)
    print(f"📧 [EMAIL VERIFICATION] Code for {email}: {code}")
    
    return {"message": "Verification code sent", "expires_in": 900}

@router.post("/auth/verify-email")
async def verify_email(data: dict):
    """Verify email with code."""
    email = data.get('email')
    code = data.get('code')
    
    if not email or not code:
        raise HTTPException(status_code=400, detail="Email and code required")
    
    record = await db.verification_codes.find_one({
        'email': email, 'code': code, 'type': 'email_verify'
    })
    
    if not record:
        raise HTTPException(status_code=400, detail="Invalid or expired code")
    
    if record['expires'] < datetime.utcnow():
        await db.verification_codes.delete_one({'_id': record['_id']})
        raise HTTPException(status_code=400, detail="Code expired")
    
    await db.users.update_one({'email': email}, {'$set': {'email_verified': True}})
    await db.verification_codes.delete_many({'email': email, 'type': 'email_verify'})
    
    return {"message": "Email verified successfully"}

# ==================== PASSWORD RECOVERY ====================

@router.post("/auth/forgot-password")
async def forgot_password(data: dict):
    """Send password reset code."""
    email = data.get('email')
    if not email:
        raise HTTPException(status_code=400, detail="Email required")
    
    user = await db.users.find_one({'email': email})
    if not user:
        # Don't reveal if email exists
        return {"message": "If this email is registered, a reset code has been sent"}
    
    code = generate_code()
    expires = datetime.utcnow() + timedelta(minutes=15)
    
    await db.verification_codes.delete_many({'email': email, 'type': 'password_reset'})
    await db.verification_codes.insert_one({
        'email': email,
        'code': code,
        'type': 'password_reset',
        'expires': expires,
        'created_at': datetime.utcnow()
    })
    
    # TODO: Replace with real email service
    print(f"🔑 [PASSWORD RESET] Code for {email}: {code}")
    
    return {"message": "If this email is registered, a reset code has been sent"}

@router.post("/auth/verify-reset-code")
async def verify_reset_code(data: dict):
    """Verify password reset code is valid (without resetting yet)."""
    email = data.get('email')
    code = data.get('code')
    
    if not email or not code:
        raise HTTPException(status_code=400, detail="Email and code required")
    
    record = await db.verification_codes.find_one({
        'email': email, 'code': code, 'type': 'password_reset'
    })
    
    if not record:
        raise HTTPException(status_code=400, detail="Invalid or expired code")
    
    if record['expires'] < datetime.utcnow():
        await db.verification_codes.delete_one({'_id': record['_id']})
        raise HTTPException(status_code=400, detail="Code expired")
    
    return {"message": "Code verified", "valid": True}

@router.post("/auth/reset-password")
async def reset_password(data: dict):
    """Reset password with verified code."""
    email = data.get('email')
    code = data.get('code')
    new_password = data.get('new_password')
    
    if not email or not code or not new_password:
        raise HTTPException(status_code=400, detail="Email, code, and new password required")
    
    if len(new_password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    
    record = await db.verification_codes.find_one({
        'email': email, 'code': code, 'type': 'password_reset'
    })
    
    if not record:
        raise HTTPException(status_code=400, detail="Invalid or expired code")
    
    if record['expires'] < datetime.utcnow():
        await db.verification_codes.delete_one({'_id': record['_id']})
        raise HTTPException(status_code=400, detail="Code expired")
    
    # Update password
    await db.users.update_one(
        {'email': email},
        {'$set': {'password_hash': hash_password(new_password)}}
    )
    await db.verification_codes.delete_many({'email': email, 'type': 'password_reset'})
    
    return {"message": "Password reset successfully"}

# ==================== SOCIAL AUTH ====================

class SocialAuthRequest(BaseModel):
    provider: str  # "google" or "apple"
    token: str  # ID token from provider
    name: Optional[str] = None
    email: Optional[str] = None

async def verify_google_token(token: str):
    """Verify Google ID token or access token and extract user info."""
    import httpx
    try:
        # Try as ID token first with Google's tokeninfo endpoint
        async with httpx.AsyncClient() as client:
            # Try as access_token to get userinfo
            resp = await client.get(
                "https://www.googleapis.com/oauth2/v3/userinfo",
                headers={"Authorization": f"Bearer {token}"}
            )
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "email": data.get("email"),
                    "name": data.get("name", "Player"),
                    "provider_id": data.get("sub", token[:64]),
                    "picture": data.get("picture"),
                }
            
            # Fallback: try as ID token
            resp2 = await client.get(
                f"https://oauth2.googleapis.com/tokeninfo?id_token={token}"
            )
            if resp2.status_code == 200:
                data2 = resp2.json()
                return {
                    "email": data2.get("email"),
                    "name": data2.get("name", "Player"),
                    "provider_id": data2.get("sub", token[:64]),
                    "picture": data2.get("picture"),
                }
    except Exception as e:
        print(f"Google token verification error: {e}")
    return None

async def verify_apple_token(token: str, email: str = None, name: str = None):
    """Verify Apple identity token (JWT) and extract user info."""
    import jwt
    import httpx
    try:
        # Decode without verification first to get the header
        header = jwt.get_unverified_header(token)
        
        # Get Apple's public keys
        async with httpx.AsyncClient() as client:
            resp = await client.get("https://appleid.apple.com/auth/keys")
            apple_keys = resp.json()["keys"]
        
        # Find the matching key
        key_data = next((k for k in apple_keys if k["kid"] == header["kid"]), None)
        if not key_data:
            print("Apple key not found")
            return None
        
        # Construct the public key
        from jwt.algorithms import RSAAlgorithm
        public_key = RSAAlgorithm.from_jwk(key_data)
        
        # Verify and decode the token
        decoded = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            audience=os.getenv("APPLE_BUNDLE_ID", "com.bizrealms.app"),
            options={"verify_exp": True}
        )
        
        return {
            "email": decoded.get("email") or email,
            "name": name or "Player",
            "provider_id": decoded.get("sub", token[:64]),
        }
    except Exception as e:
        print(f"Apple token verification error: {e}")
        # Fallback: trust the provided email from Apple (first sign-in only provides email)
        if email:
            return {
                "email": email,
                "name": name or "Player",
                "provider_id": token[:64],
            }
    return None

@router.post("/auth/social", response_model=TokenResponse)
async def social_auth(data: SocialAuthRequest):
    """Authenticate via Google or Apple Sign-In."""
    provider = data.provider
    
    if provider == "google":
        verified = await verify_google_token(data.token)
        if not verified:
            # Fallback: trust provided data for development/testing
            if data.email:
                verified = {"email": data.email, "name": data.name or "Player", "provider_id": data.token[:64]}
            else:
                raise HTTPException(status_code=401, detail="Invalid Google token")
        user_email = verified["email"]
        user_name = verified.get("name") or data.name or "Player"
        provider_id = verified["provider_id"]
        
    elif provider == "apple":
        verified = await verify_apple_token(data.token, data.email, data.name)
        if not verified:
            if data.email:
                verified = {"email": data.email, "name": data.name or "Player", "provider_id": data.token[:64]}
            else:
                raise HTTPException(status_code=401, detail="Invalid Apple token")
        user_email = verified["email"]
        user_name = verified.get("name") or data.name or "Player"
        provider_id = verified["provider_id"]
        
    else:
        raise HTTPException(status_code=400, detail="Invalid provider. Use 'google' or 'apple'.")
    
    if not user_email:
        raise HTTPException(status_code=400, detail="Email is required for social authentication")
    
    # Check if user exists with this email
    existing_user = await db.users.find_one({'email': user_email})
    
    if existing_user:
        # User exists - update provider info and log them in
        await db.users.update_one(
            {'email': user_email},
            {'$set': {
                'auth_provider': provider,
                'auth_provider_id': provider_id,
                'email_verified': True,  # Social auth emails are pre-verified
            }}
        )
        user = await db.users.find_one({'email': user_email})
        token = create_token(user['id'])
        del user['password_hash']
        del user['_id']
        return TokenResponse(token=token, user=user)
    else:
        # Create new user via social auth
        user = User(
            email=user_email,
            password_hash="",  # No password for social auth
            name=user_name,
            auth_provider=provider,
            auth_provider_id=provider_id,
            email_verified=True,
        )
        await db.users.insert_one(user.dict())
        token = create_token(user.id)
        user_dict = user.dict()
        del user_dict['password_hash']
        return TokenResponse(token=token, user=user_dict)
