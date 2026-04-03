#!/usr/bin/env python3
"""
Additional verification tests for Push Notification and Social Auth
"""

import requests
import json
from datetime import datetime

# Configuration
BACKEND_URL = "https://career-mogul-1.preview.emergentagent.com/api"
TEST_EMAIL = "teste@businessempire.com"
TEST_PASSWORD = "teste123"

def log(message):
    """Log test messages with timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")

def test_additional_scenarios():
    """Test additional edge cases and scenarios"""
    session = requests.Session()
    
    # Login
    log("🔐 Logging in for additional tests...")
    response = session.post(f"{BACKEND_URL}/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    
    if response.status_code != 200:
        log(f"❌ Login failed: {response.status_code}")
        return False
    
    token = response.json()["token"]
    session.headers.update({"Authorization": f"Bearer {token}"})
    log("✅ Login successful")
    
    # Test 1: Push registration with missing token
    log("\n📱 Testing Push Registration with missing token...")
    response = session.post(f"{BACKEND_URL}/push/register", json={"platform": "ios"})
    if response.status_code == 400:
        log("✅ Missing push token properly rejected")
    else:
        log(f"❌ Expected 400 for missing token, got {response.status_code}")
    
    # Test 2: Push send with custom data payload
    log("\n📤 Testing Push Send with custom data...")
    # First register a token
    session.post(f"{BACKEND_URL}/push/register", json={
        "push_token": "ExponentPushToken[test456]",
        "platform": "android"
    })
    
    response = session.post(f"{BACKEND_URL}/push/send", json={
        "title": "Custom Test",
        "body": "Test with data",
        "data": {"action": "open_screen", "screen": "profile"}
    })
    if response.status_code == 200:
        log("✅ Push send with custom data successful")
        log(f"   Response: {response.json()}")
    else:
        log(f"❌ Push send with data failed: {response.status_code}")
    
    # Test 3: Social auth with Apple provider
    log("\n🔐 Testing Social Auth with Apple provider...")
    # Remove auth header for social auth test
    headers = session.headers.copy()
    if "Authorization" in session.headers:
        del session.headers["Authorization"]
    
    response = session.post(f"{BACKEND_URL}/auth/social", json={
        "provider": "apple",
        "token": "apple_test_token",
        "email": "apple@test.com",
        "name": "Apple User"
    })
    
    # Restore auth header
    session.headers = headers
    
    if response.status_code == 200:
        log("✅ Apple social auth successful")
        data = response.json()
        log(f"   User: {data.get('user', {}).get('email', 'N/A')}")
    else:
        log(f"❌ Apple social auth failed: {response.status_code}")
    
    # Test 4: Social auth with existing user (should login, not create new)
    log("\n🔐 Testing Social Auth with existing user...")
    # Remove auth header
    headers = session.headers.copy()
    if "Authorization" in session.headers:
        del session.headers["Authorization"]
    
    response = session.post(f"{BACKEND_URL}/auth/social", json={
        "provider": "google",
        "token": "existing_user_token",
        "email": "social@test.com",  # This user was created in previous test
        "name": "Updated Social User"
    })
    
    # Restore auth header
    session.headers = headers
    
    if response.status_code == 200:
        log("✅ Existing user social auth successful (login)")
        data = response.json()
        log(f"   User: {data.get('user', {}).get('email', 'N/A')}")
    else:
        log(f"❌ Existing user social auth failed: {response.status_code}")
    
    # Test 5: Social auth without email
    log("\n🔐 Testing Social Auth without email...")
    # Remove auth header
    headers = session.headers.copy()
    if "Authorization" in session.headers:
        del session.headers["Authorization"]
    
    response = session.post(f"{BACKEND_URL}/auth/social", json={
        "provider": "google",
        "token": "no_email_token",
        "name": "No Email User"
    })
    
    # Restore auth header
    session.headers = headers
    
    if response.status_code == 400:
        log("✅ Social auth without email properly rejected")
        log(f"   Error: {response.json().get('detail', 'N/A')}")
    else:
        log(f"❌ Expected 400 for missing email, got {response.status_code}")
    
    log("\n✅ Additional verification tests completed")
    return True

if __name__ == "__main__":
    test_additional_scenarios()