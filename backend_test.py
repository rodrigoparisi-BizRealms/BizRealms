#!/usr/bin/env python3
"""
Backend API Testing Script for BizRealms
Tests Push Notification and Social Auth endpoints
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BACKEND_URL = "https://career-mogul-1.preview.emergentagent.com/api"
TEST_EMAIL = "teste@businessempire.com"
TEST_PASSWORD = "teste123"

class BizRealmsAPITester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.user_id = None
        
    def log(self, message):
        """Log test messages with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")
        
    def login(self):
        """Login to get JWT token"""
        self.log("🔐 Logging in...")
        
        response = self.session.post(f"{BACKEND_URL}/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        if response.status_code == 200:
            data = response.json()
            self.token = data["token"]
            self.user_id = data["user"]["id"]
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
            self.log(f"✅ Login successful. User ID: {self.user_id}")
            return True
        else:
            self.log(f"❌ Login failed: {response.status_code} - {response.text}")
            return False
    
    def test_push_register(self):
        """Test push notification token registration"""
        self.log("\n📱 Testing Push Notification Registration...")
        
        test_data = {
            "push_token": "ExponentPushToken[test123]",
            "platform": "ios"
        }
        
        response = self.session.post(f"{BACKEND_URL}/push/register", json=test_data)
        
        if response.status_code == 200:
            data = response.json()
            self.log(f"✅ Push token registered successfully")
            self.log(f"   Response: {data}")
            return True
        else:
            self.log(f"❌ Push registration failed: {response.status_code} - {response.text}")
            return False
    
    def test_push_send(self):
        """Test sending push notification"""
        self.log("\n📤 Testing Push Notification Send...")
        
        test_data = {
            "title": "Test",
            "body": "Hello"
        }
        
        response = self.session.post(f"{BACKEND_URL}/push/send", json=test_data)
        
        if response.status_code == 200:
            data = response.json()
            self.log(f"✅ Push notification send attempted")
            self.log(f"   Response: {data}")
            # Note: This may return 0 sent since token is fake, but should not crash
            return True
        else:
            self.log(f"❌ Push send failed: {response.status_code} - {response.text}")
            return False
    
    def test_push_unregister(self):
        """Test push notification token unregistration"""
        self.log("\n📱❌ Testing Push Notification Unregistration...")
        
        response = self.session.delete(f"{BACKEND_URL}/push/unregister")
        
        if response.status_code == 200:
            data = response.json()
            self.log(f"✅ Push token unregistered successfully")
            self.log(f"   Response: {data}")
            return True
        else:
            self.log(f"❌ Push unregistration failed: {response.status_code} - {response.text}")
            return False
    
    def test_social_auth_valid(self):
        """Test social auth with valid provider"""
        self.log("\n🔐 Testing Social Auth (Valid Provider)...")
        
        test_data = {
            "provider": "google",
            "token": "test_token",
            "email": "social@test.com",
            "name": "Social User"
        }
        
        # Remove auth header for this test since it's a login endpoint
        headers = self.session.headers.copy()
        if "Authorization" in self.session.headers:
            del self.session.headers["Authorization"]
        
        response = self.session.post(f"{BACKEND_URL}/auth/social", json=test_data)
        
        # Restore auth header
        self.session.headers = headers
        
        if response.status_code == 200:
            data = response.json()
            self.log(f"✅ Social auth successful")
            self.log(f"   User created/logged in: {data.get('user', {}).get('email', 'N/A')}")
            self.log(f"   Token received: {'Yes' if data.get('token') else 'No'}")
            return True
        else:
            self.log(f"❌ Social auth failed: {response.status_code} - {response.text}")
            return False
    
    def test_social_auth_invalid_provider(self):
        """Test social auth with invalid provider"""
        self.log("\n🔐❌ Testing Social Auth (Invalid Provider)...")
        
        test_data = {
            "provider": "invalid_provider",
            "token": "test_token",
            "email": "social@test.com",
            "name": "Social User"
        }
        
        # Remove auth header for this test
        headers = self.session.headers.copy()
        if "Authorization" in self.session.headers:
            del self.session.headers["Authorization"]
        
        response = self.session.post(f"{BACKEND_URL}/auth/social", json=test_data)
        
        # Restore auth header
        self.session.headers = headers
        
        if response.status_code == 400:
            self.log(f"✅ Invalid provider properly rejected")
            self.log(f"   Error message: {response.json().get('detail', 'N/A')}")
            return True
        else:
            self.log(f"❌ Invalid provider test failed: Expected 400, got {response.status_code}")
            return False
    
    def test_push_without_auth(self):
        """Test push endpoints without authentication"""
        self.log("\n🔐❌ Testing Push Endpoints Without Auth...")
        
        # Remove auth header
        headers = self.session.headers.copy()
        if "Authorization" in self.session.headers:
            del self.session.headers["Authorization"]
        
        # Test register without auth
        response = self.session.post(f"{BACKEND_URL}/push/register", json={
            "push_token": "ExponentPushToken[test123]",
            "platform": "ios"
        })
        
        auth_required = response.status_code == 403
        
        # Restore auth header
        self.session.headers = headers
        
        if auth_required:
            self.log(f"✅ Push endpoints properly require authentication")
            return True
        else:
            self.log(f"❌ Push endpoints should require authentication but got: {response.status_code}")
            return False
    
    def run_all_tests(self):
        """Run all tests"""
        self.log("🚀 Starting BizRealms Push Notification & Social Auth API Tests")
        self.log(f"Backend URL: {BACKEND_URL}")
        
        # Login first
        if not self.login():
            self.log("❌ Cannot proceed without login")
            return False
        
        # Track test results
        tests = [
            ("Push Registration", self.test_push_register),
            ("Push Send", self.test_push_send),
            ("Push Unregistration", self.test_push_unregister),
            ("Social Auth (Valid)", self.test_social_auth_valid),
            ("Social Auth (Invalid Provider)", self.test_social_auth_invalid_provider),
            ("Push Auth Required", self.test_push_without_auth),
        ]
        
        results = []
        for test_name, test_func in tests:
            try:
                result = test_func()
                results.append((test_name, result))
            except Exception as e:
                self.log(f"❌ {test_name} crashed: {e}")
                results.append((test_name, False))
        
        # Summary
        self.log("\n" + "="*60)
        self.log("📊 TEST SUMMARY")
        self.log("="*60)
        
        passed = 0
        total = len(results)
        
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            self.log(f"{status} - {test_name}")
            if result:
                passed += 1
        
        self.log(f"\nResults: {passed}/{total} tests passed")
        
        if passed == total:
            self.log("🎉 All tests passed!")
            return True
        else:
            self.log(f"⚠️  {total - passed} tests failed")
            return False

if __name__ == "__main__":
    tester = BizRealmsAPITester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)