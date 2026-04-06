#!/usr/bin/env python3
"""
Backend Testing Script for Public Profile Endpoint Fix
Tests the specific endpoints requested in the review.
"""

import requests
import json
import sys

# Backend URL from frontend .env
BACKEND_URL = "https://career-mogul-1.preview.emergentagent.com"

# Test credentials from /app/memory/test_credentials.md
TEST_EMAIL = "teste@businessempire.com"
TEST_PASSWORD = "teste123"

def test_public_profile_endpoint():
    """Test the public profile endpoint fix as requested"""
    print("🧪 TESTING PUBLIC PROFILE ENDPOINT FIX")
    print("=" * 50)
    
    session = requests.Session()
    
    # Test 1: Login
    print("\n1️⃣ Testing Login - POST /api/auth/login")
    login_data = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    }
    
    try:
        login_response = session.post(f"{BACKEND_URL}/api/auth/login", json=login_data)
        print(f"Status: {login_response.status_code}")
        
        if login_response.status_code == 200:
            login_result = login_response.json()
            print(f"Login response: {login_result}")
            token = login_result.get("token")  # Changed from access_token to token
            if token:
                print(f"✅ Login successful - Token received: {token[:20]}...")
                # Set authorization header for subsequent requests
                session.headers.update({"Authorization": f"Bearer {token}"})
            else:
                print(f"❌ No token in response: {login_result}")
                return False
        else:
            print(f"❌ Login failed: {login_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Login error: {str(e)}")
        return False
    
    # Test 2: Get user ID from /api/user/me
    print("\n2️⃣ Testing Get User ID - GET /api/user/me")
    try:
        me_response = session.get(f"{BACKEND_URL}/api/user/me")
        print(f"Status: {me_response.status_code}")
        
        if me_response.status_code == 200:
            user_data = me_response.json()
            user_id = user_data.get("id")
            print(f"✅ User profile retrieved - User ID: {user_id}")
            print(f"User name: {user_data.get('name')}")
            print(f"User level: {user_data.get('level')}")
            print(f"User money: R$ {user_data.get('money', 0):,.2f}")
        else:
            print(f"❌ Get user profile failed: {me_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Get user profile error: {str(e)}")
        return False
    
    # Test 3: Public Profile - GET /api/user/profile/{user_id}
    print(f"\n3️⃣ Testing Public Profile - GET /api/user/profile/{user_id}")
    try:
        profile_response = session.get(f"{BACKEND_URL}/api/user/profile/{user_id}")
        print(f"Status: {profile_response.status_code}")
        
        if profile_response.status_code == 200:
            profile_data = profile_response.json()
            print("✅ Public profile retrieved successfully!")
            print(f"Profile data structure:")
            
            # Check required fields as mentioned in the request
            required_fields = ["name", "level", "money", "companies_count", "comparison"]
            
            for field in required_fields:
                if field in profile_data:
                    print(f"  ✅ {field}: {profile_data[field]}")
                else:
                    print(f"  ❌ Missing field: {field}")
            
            # Show full profile data for verification
            print(f"\nFull profile response:")
            print(json.dumps(profile_data, indent=2, ensure_ascii=False))
            
        else:
            print(f"❌ Public profile failed: {profile_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Public profile error: {str(e)}")
        return False
    
    print("\n🎉 PUBLIC PROFILE ENDPOINT TESTING COMPLETE!")
    return True

if __name__ == "__main__":
    success = test_public_profile_endpoint()
    sys.exit(0 if success else 1)