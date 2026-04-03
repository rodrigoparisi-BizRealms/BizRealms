#!/usr/bin/env python3
"""
BizRealms Backend Smoke Test
Quick verification of key endpoints after refactoring
"""

import requests
import json
import sys

# Configuration
BASE_URL = "https://career-mogul-1.preview.emergentagent.com/api"
TEST_EMAIL = "teste@businessempire.com"
TEST_PASSWORD = "teste123"

def test_login():
    """Test login endpoint and get JWT token"""
    print("🔐 Testing login endpoint...")
    
    login_data = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data, timeout=10)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("token")  # Check for 'token' field
            if not token:
                token = data.get("access_token")  # Fallback to 'access_token'
            
            if token:
                print("   ✅ Login successful, JWT token received")
                return token
            else:
                print("   ❌ Login response missing token")
                print(f"   Response: {data}")
                return None
        else:
            print(f"   ❌ Login failed: {response.text}")
            return None
            
    except Exception as e:
        print(f"   ❌ Login error: {str(e)}")
        return None

def test_authenticated_endpoint(endpoint, token, description):
    """Test an authenticated endpoint"""
    print(f"🔍 Testing {description}...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{BASE_URL}{endpoint}", headers=headers, timeout=10)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            print(f"   ✅ {description} - OK")
            return True
        else:
            print(f"   ❌ {description} failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ {description} error: {str(e)}")
        return False

def test_public_endpoint(endpoint, description):
    """Test a public endpoint (no auth required)"""
    print(f"🌐 Testing {description}...")
    
    try:
        response = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            print(f"   ✅ {description} - OK")
            return True
        else:
            print(f"   ❌ {description} failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ {description} error: {str(e)}")
        return False

def main():
    """Run smoke test for BizRealms backend"""
    print("🚀 BizRealms Backend Smoke Test")
    print("=" * 50)
    
    # Step 1: Login and get token
    token = test_login()
    if not token:
        print("\n❌ SMOKE TEST FAILED: Cannot login")
        sys.exit(1)
    
    print()
    
    # Step 2: Test authenticated endpoints
    authenticated_tests = [
        ("/user/me", "GET /api/user/me - Get user profile"),
        ("/user/stats", "GET /api/user/stats - Get user stats"),
        ("/notifications", "GET /api/notifications - Get notifications"),
        ("/achievements", "GET /api/achievements - Get achievements"),
        ("/store/items", "GET /api/store/items - Get store items"),
        ("/investments/market", "GET /api/investments/market - Get investment market")
    ]
    
    auth_results = []
    for endpoint, description in authenticated_tests:
        result = test_authenticated_endpoint(endpoint, token, description)
        auth_results.append(result)
        print()
    
    # Step 3: Test public endpoints
    public_tests = [
        ("/legal/terms", "GET /api/legal/terms - Public legal terms"),
        ("/legal/privacy", "GET /api/legal/privacy - Public privacy policy")
    ]
    
    public_results = []
    for endpoint, description in public_tests:
        result = test_public_endpoint(endpoint, description)
        public_results.append(result)
        print()
    
    # Summary
    total_tests = len(auth_results) + len(public_results) + 1  # +1 for login
    passed_tests = sum(auth_results) + sum(public_results) + (1 if token else 0)
    
    print("=" * 50)
    print("📊 SMOKE TEST SUMMARY")
    print(f"Total tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    
    if passed_tests == total_tests:
        print("\n🎉 ALL SMOKE TESTS PASSED!")
        print("✅ Backend refactoring successful - no regressions detected")
        return True
    else:
        print(f"\n❌ SMOKE TEST FAILED: {total_tests - passed_tests} endpoint(s) not working")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)