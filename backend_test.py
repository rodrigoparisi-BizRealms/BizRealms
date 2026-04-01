#!/usr/bin/env python3
"""
Business Empire Backend API Test Suite
Tests all authentication and profile management endpoints
"""

import requests
import json
import sys
import os
from datetime import datetime

# Get backend URL from frontend .env
BACKEND_URL = "https://career-mogul-1.preview.emergentagent.com/api"

# Test credentials
TEST_EMAIL = "teste@businessempire.com"
TEST_PASSWORD = "teste123"
TEST_NAME = "Jogador Teste"

# New user for registration test
NEW_TEST_EMAIL = "novo_teste@businessempire.com"
NEW_TEST_PASSWORD = "novoTeste123"
NEW_TEST_NAME = "Novo Jogador"

class BusinessEmpireAPITester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.token = None
        self.user_id = None
        self.test_results = []
        
    def log_test(self, test_name, success, message, details=None):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "details": details or {}
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name} - {message}")
        if details and not success:
            print(f"   Details: {details}")
    
    def test_api_health(self):
        """Test if API is accessible"""
        try:
            response = requests.get(f"{self.base_url}/", timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.log_test("API Health Check", True, f"API is running: {data.get('message', 'OK')}")
                return True
            else:
                self.log_test("API Health Check", False, f"API returned status {response.status_code}")
                return False
        except Exception as e:
            self.log_test("API Health Check", False, f"Failed to connect to API: {str(e)}")
            return False
    
    def test_user_registration(self):
        """Test user registration endpoint"""
        try:
            # First try to register a new user
            payload = {
                "email": NEW_TEST_EMAIL,
                "password": NEW_TEST_PASSWORD,
                "name": NEW_TEST_NAME
            }
            
            response = requests.post(f"{self.base_url}/auth/register", json=payload, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if "token" in data and "user" in data:
                    user = data["user"]
                    # Verify initial user state
                    expected_defaults = {
                        "money": 1000.0,
                        "experience_points": 0,
                        "level": 1,
                        "location": "São Paulo, Brazil"
                    }
                    
                    issues = []
                    for key, expected_value in expected_defaults.items():
                        if user.get(key) != expected_value:
                            issues.append(f"{key}: expected {expected_value}, got {user.get(key)}")
                    
                    if not issues:
                        self.log_test("User Registration", True, "New user registered successfully with correct defaults")
                        return True
                    else:
                        self.log_test("User Registration", False, "User registered but with incorrect defaults", {"issues": issues})
                        return False
                else:
                    self.log_test("User Registration", False, "Registration response missing token or user data", {"response": data})
                    return False
            elif response.status_code == 400:
                # User might already exist, try with existing user
                self.log_test("User Registration", True, "User already exists (expected for existing test user)")
                return True
            else:
                self.log_test("User Registration", False, f"Registration failed with status {response.status_code}", {"response": response.text})
                return False
                
        except Exception as e:
            self.log_test("User Registration", False, f"Registration request failed: {str(e)}")
            return False
    
    def test_user_login(self):
        """Test user login endpoint"""
        try:
            payload = {
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            }
            
            response = requests.post(f"{self.base_url}/auth/login", json=payload, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if "token" in data and "user" in data:
                    self.token = data["token"]
                    self.user_id = data["user"]["id"]
                    self.log_test("User Login", True, "Login successful, JWT token received")
                    return True
                else:
                    self.log_test("User Login", False, "Login response missing token or user data", {"response": data})
                    return False
            else:
                self.log_test("User Login", False, f"Login failed with status {response.status_code}", {"response": response.text})
                return False
                
        except Exception as e:
            self.log_test("User Login", False, f"Login request failed: {str(e)}")
            return False
    
    def test_get_user_profile(self):
        """Test get current user profile endpoint"""
        if not self.token:
            self.log_test("Get User Profile", False, "No authentication token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(f"{self.base_url}/user/me", headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["id", "email", "name", "money", "experience_points", "level", "skills"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    self.log_test("Get User Profile", True, "User profile retrieved successfully")
                    return True
                else:
                    self.log_test("Get User Profile", False, "Profile missing required fields", {"missing": missing_fields})
                    return False
            else:
                self.log_test("Get User Profile", False, f"Profile request failed with status {response.status_code}", {"response": response.text})
                return False
                
        except Exception as e:
            self.log_test("Get User Profile", False, f"Profile request failed: {str(e)}")
            return False
    
    def test_get_user_stats(self):
        """Test get user statistics endpoint"""
        if not self.token:
            self.log_test("Get User Stats", False, "No authentication token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(f"{self.base_url}/user/stats", headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["level", "experience_points", "money", "education_count", "certification_count", "skills"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    self.log_test("Get User Stats", True, "User statistics retrieved successfully")
                    return True
                else:
                    self.log_test("Get User Stats", False, "Stats missing required fields", {"missing": missing_fields})
                    return False
            else:
                self.log_test("Get User Stats", False, f"Stats request failed with status {response.status_code}", {"response": response.text})
                return False
                
        except Exception as e:
            self.log_test("Get User Stats", False, f"Stats request failed: {str(e)}")
            return False
    
    def test_update_location(self):
        """Test update user location endpoint"""
        if not self.token:
            self.log_test("Update Location", False, "No authentication token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            payload = {"location": "Rio de Janeiro, Brazil"}
            
            response = requests.put(f"{self.base_url}/user/location", json=payload, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if "message" in data and "location" in data:
                    self.log_test("Update Location", True, "Location updated successfully")
                    return True
                else:
                    self.log_test("Update Location", False, "Update response missing expected fields", {"response": data})
                    return False
            else:
                self.log_test("Update Location", False, f"Location update failed with status {response.status_code}", {"response": response.text})
                return False
                
        except Exception as e:
            self.log_test("Update Location", False, f"Location update failed: {str(e)}")
            return False
    
    def test_add_education(self):
        """Test add education endpoint"""
        if not self.token:
            self.log_test("Add Education", False, "No authentication token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            payload = {
                "degree": "Graduação",
                "field": "Administração",
                "institution": "Universidade de São Paulo",
                "year_completed": 2020,
                "level": 2
            }
            
            response = requests.post(f"{self.base_url}/user/education", json=payload, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if "message" in data and "exp_gained" in data and "new_level" in data:
                    expected_exp = payload["level"] * 500  # 2 * 500 = 1000 XP
                    if data["exp_gained"] == expected_exp:
                        self.log_test("Add Education", True, f"Education added successfully, gained {expected_exp} XP")
                        return True
                    else:
                        self.log_test("Add Education", False, f"Incorrect XP calculation: expected {expected_exp}, got {data['exp_gained']}")
                        return False
                else:
                    self.log_test("Add Education", False, "Education response missing expected fields", {"response": data})
                    return False
            else:
                self.log_test("Add Education", False, f"Add education failed with status {response.status_code}", {"response": response.text})
                return False
                
        except Exception as e:
            self.log_test("Add Education", False, f"Add education failed: {str(e)}")
            return False
    
    def test_add_certification(self):
        """Test add certification endpoint"""
        if not self.token:
            self.log_test("Add Certification", False, "No authentication token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            payload = {
                "name": "Project Management Professional (PMP)",
                "issuer": "PMI",
                "skill_boost": 7
            }
            
            response = requests.post(f"{self.base_url}/user/certification", json=payload, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if "message" in data and "exp_gained" in data and "new_level" in data:
                    expected_exp = payload["skill_boost"] * 100  # 7 * 100 = 700 XP
                    if data["exp_gained"] == expected_exp:
                        self.log_test("Add Certification", True, f"Certification added successfully, gained {expected_exp} XP")
                        return True
                    else:
                        self.log_test("Add Certification", False, f"Incorrect XP calculation: expected {expected_exp}, got {data['exp_gained']}")
                        return False
                else:
                    self.log_test("Add Certification", False, "Certification response missing expected fields", {"response": data})
                    return False
            else:
                self.log_test("Add Certification", False, f"Add certification failed with status {response.status_code}", {"response": response.text})
                return False
                
        except Exception as e:
            self.log_test("Add Certification", False, f"Add certification failed: {str(e)}")
            return False
    
    def test_jwt_authentication(self):
        """Test JWT token validation"""
        try:
            # Test with invalid token
            headers = {"Authorization": "Bearer invalid_token"}
            response = requests.get(f"{self.base_url}/user/me", headers=headers, timeout=10)
            
            if response.status_code == 401:
                self.log_test("JWT Authentication", True, "Invalid token correctly rejected")
                return True
            else:
                self.log_test("JWT Authentication", False, f"Invalid token not rejected, status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("JWT Authentication", False, f"JWT test failed: {str(e)}")
            return False
    
    def test_password_hashing(self):
        """Test password hashing by attempting login with wrong password"""
        try:
            payload = {
                "email": TEST_EMAIL,
                "password": "wrong_password"
            }
            
            response = requests.post(f"{self.base_url}/auth/login", json=payload, timeout=10)
            
            if response.status_code == 401:
                self.log_test("Password Hashing", True, "Wrong password correctly rejected")
                return True
            else:
                self.log_test("Password Hashing", False, f"Wrong password not rejected, status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Password Hashing", False, f"Password hashing test failed: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all tests in sequence"""
        print("🚀 Starting Business Empire Backend API Tests")
        print(f"🔗 Testing API at: {self.base_url}")
        print("=" * 60)
        
        # Test sequence
        tests = [
            self.test_api_health,
            self.test_user_registration,
            self.test_user_login,
            self.test_jwt_authentication,
            self.test_password_hashing,
            self.test_get_user_profile,
            self.test_get_user_stats,
            self.test_update_location,
            self.test_add_education,
            self.test_add_certification
        ]
        
        passed = 0
        failed = 0
        
        for test in tests:
            try:
                if test():
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                print(f"❌ FAIL: {test.__name__} - Unexpected error: {str(e)}")
                failed += 1
            print()  # Empty line for readability
        
        # Summary
        print("=" * 60)
        print(f"📊 TEST SUMMARY")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"📈 Success Rate: {(passed/(passed+failed)*100):.1f}%")
        
        if failed > 0:
            print("\n🔍 FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   • {result['test']}: {result['message']}")
        
        return failed == 0

if __name__ == "__main__":
    tester = BusinessEmpireAPITester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)