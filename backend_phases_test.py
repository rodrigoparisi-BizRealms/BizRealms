#!/usr/bin/env python3
"""
BizRealms Backend Testing - Life Phases & Crises System
Comprehensive testing of the new Life Phases & Crises System endpoints.
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "https://career-mogul-1.preview.emergentagent.com/api"
TEST_EMAIL = "teste@businessempire.com"
TEST_PASSWORD = "teste123"

class BizRealmsPhasesTester:
    def __init__(self):
        self.session = requests.Session()
        self.jwt_token = None
        self.user_data = None
        self.test_results = []
        self.generated_crisis = None
        
    def log_test(self, test_name, success, details="", response_data=None):
        """Log test results"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat(),
            "response_data": response_data
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {details}")
        if response_data and not success:
            print(f"   Response: {json.dumps(response_data, indent=2)}")
    
    def login(self):
        """Login and get JWT token"""
        print(f"\n🔐 Logging in as {TEST_EMAIL}...")
        
        try:
            response = self.session.post(f"{BASE_URL}/auth/login", json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            })
            
            if response.status_code == 200:
                data = response.json()
                self.jwt_token = data.get("token")
                self.user_data = data.get("user", {})
                
                # Set authorization header for all future requests
                self.session.headers.update({
                    "Authorization": f"Bearer {self.jwt_token}"
                })
                
                self.log_test("Login", True, f"Successfully logged in. User ID: {self.user_data.get('id', 'N/A')}")
                return True
            else:
                self.log_test("Login", False, f"Login failed with status {response.status_code}", response.json())
                return False
                
        except Exception as e:
            self.log_test("Login", False, f"Login exception: {str(e)}")
            return False
    
    def test_get_current_phase(self):
        """Test GET /api/phases/current - Get current life phase"""
        print("\n📊 Testing GET /api/phases/current...")
        
        try:
            response = self.session.get(f"{BASE_URL}/phases/current")
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["phase", "progress", "net_worth", "phase_index", "total_phases", "company_count"]
                
                if all(field in data for field in required_fields):
                    phase = data.get("phase", {})
                    phase_required = ["id", "name", "emoji", "color", "bonuses", "unlocks", "tips"]
                    
                    if all(field in phase for field in phase_required):
                        bonuses = phase.get("bonuses", {})
                        bonus_fields = ["xp_multiplier", "income_bonus", "company_slots", "investment_bonus"]
                        
                        if all(field in bonuses for field in bonus_fields):
                            next_phase = data.get("next_phase")
                            if next_phase is None or isinstance(next_phase, dict):
                                self.log_test("GET /api/phases/current", True, 
                                            f"Current phase: {phase['name']} ({phase['id']}), Net worth: R$ {data['net_worth']}, Progress: {data['progress']:.2%}")
                                return True
                            else:
                                self.log_test("GET /api/phases/current", False, 
                                            "Invalid next_phase structure", data)
                                return False
                        else:
                            self.log_test("GET /api/phases/current", False, 
                                        f"Missing bonus fields. Expected: {bonus_fields}", data)
                            return False
                    else:
                        self.log_test("GET /api/phases/current", False, 
                                    f"Missing phase fields. Expected: {phase_required}", data)
                        return False
                else:
                    self.log_test("GET /api/phases/current", False, 
                                f"Missing required fields. Expected: {required_fields}", data)
                    return False
            else:
                self.log_test("GET /api/phases/current", False, 
                            f"HTTP {response.status_code}", response.json())
                return False
                
        except Exception as e:
            self.log_test("GET /api/phases/current", False, f"Exception: {str(e)}")
            return False
    
    def test_get_all_phases(self):
        """Test GET /api/phases/all - Get all 4 phase definitions"""
        print("\n📋 Testing GET /api/phases/all...")
        
        try:
            response = self.session.get(f"{BASE_URL}/phases/all")
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["phases", "current_net_worth"]
                
                if all(field in data for field in required_fields):
                    phases = data.get("phases", [])
                    
                    if len(phases) == 4:  # Should have exactly 4 phases
                        expected_phase_ids = ["survival", "growth", "empire", "influence"]
                        phase_ids = [p.get("id") for p in phases]
                        
                        if all(pid in phase_ids for pid in expected_phase_ids):
                            # Validate phase structure
                            valid_phases = True
                            current_count = 0
                            unlocked_count = 0
                            
                            for phase in phases:
                                phase_fields = ["id", "name", "emoji", "color", "bonuses", "unlocks", "min_net_worth", "is_current", "is_unlocked"]
                                if not all(field in phase for field in phase_fields):
                                    valid_phases = False
                                    break
                                
                                if phase.get("is_current"):
                                    current_count += 1
                                if phase.get("is_unlocked"):
                                    unlocked_count += 1
                            
                            if valid_phases and current_count == 1:  # Exactly one current phase
                                self.log_test("GET /api/phases/all", True, 
                                            f"All 4 phases retrieved. Current net worth: R$ {data['current_net_worth']}, Unlocked: {unlocked_count}/4")
                                return True
                            else:
                                self.log_test("GET /api/phases/all", False, 
                                            f"Invalid phase structure or current count: {current_count}", data)
                                return False
                        else:
                            self.log_test("GET /api/phases/all", False, 
                                        f"Missing expected phase IDs. Expected: {expected_phase_ids}, Got: {phase_ids}", data)
                            return False
                    else:
                        self.log_test("GET /api/phases/all", False, 
                                    f"Expected 4 phases, got {len(phases)}", data)
                        return False
                else:
                    self.log_test("GET /api/phases/all", False, 
                                f"Missing required fields. Expected: {required_fields}", data)
                    return False
            else:
                self.log_test("GET /api/phases/all", False, 
                            f"HTTP {response.status_code}", response.json())
                return False
                
        except Exception as e:
            self.log_test("GET /api/phases/all", False, f"Exception: {str(e)}")
            return False
    
    def test_get_active_crises_empty(self):
        """Test GET /api/crises/active - Check for active crises (should be empty initially)"""
        print("\n🚨 Testing GET /api/crises/active (empty state)...")
        
        try:
            response = self.session.get(f"{BASE_URL}/crises/active")
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["crises", "count"]
                
                if all(field in data for field in required_fields):
                    crises = data.get("crises", [])
                    count = data.get("count", 0)
                    
                    if len(crises) == count:
                        self.log_test("GET /api/crises/active (empty)", True, 
                                    f"Active crises retrieved: {count} crises")
                        return True
                    else:
                        self.log_test("GET /api/crises/active (empty)", False, 
                                    f"Count mismatch: crises length={len(crises)}, count={count}", data)
                        return False
                else:
                    self.log_test("GET /api/crises/active (empty)", False, 
                                f"Missing required fields. Expected: {required_fields}", data)
                    return False
            else:
                self.log_test("GET /api/crises/active (empty)", False, 
                            f"HTTP {response.status_code}", response.json())
                return False
                
        except Exception as e:
            self.log_test("GET /api/crises/active (empty)", False, f"Exception: {str(e)}")
            return False
    
    def test_check_crisis_generation(self):
        """Test POST /api/crises/check - Attempt to generate a crisis"""
        print("\n🎲 Testing POST /api/crises/check...")
        
        try:
            response = self.session.post(f"{BASE_URL}/crises/check")
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("generated") is True and "crisis" in data:
                    # Crisis was generated
                    crisis = data["crisis"]
                    required_fields = ["id", "type", "title", "emoji", "color", "description", "severity", "phase", "options", "status"]
                    
                    if all(field in crisis for field in required_fields):
                        options = crisis.get("options", [])
                        if len(options) >= 2:  # Should have at least 2 options
                            # Validate option structure
                            option_valid = True
                            for option in options:
                                if not all(field in option for field in ["id", "text", "cost_pct", "xp"]):
                                    option_valid = False
                                    break
                            
                            if option_valid:
                                self.log_test("POST /api/crises/check", True, 
                                            f"Crisis generated: {crisis['title']} ({crisis['severity']}), Options: {len(options)}")
                                self.generated_crisis = crisis  # Store for later tests
                                return True
                            else:
                                self.log_test("POST /api/crises/check", False, 
                                            "Invalid option structure", data)
                                return False
                        else:
                            self.log_test("POST /api/crises/check", False, 
                                        f"Insufficient options: {len(options)}", data)
                            return False
                    else:
                        self.log_test("POST /api/crises/check", False, 
                                    f"Missing required crisis fields. Expected: {required_fields}", data)
                        return False
                elif data.get("generated") is False:
                    # Crisis not generated due to cooldown, existing crisis, or probability
                    reason = data.get("reason", "Unknown reason")
                    self.log_test("POST /api/crises/check", True, 
                                f"Crisis not generated (expected): {reason}")
                    return True
                else:
                    self.log_test("POST /api/crises/check", False, 
                                "Unexpected response structure", data)
                    return False
            else:
                self.log_test("POST /api/crises/check", False, 
                            f"HTTP {response.status_code}", response.json())
                return False
                
        except Exception as e:
            self.log_test("POST /api/crises/check", False, f"Exception: {str(e)}")
            return False
    
    def test_resolve_crisis(self):
        """Test POST /api/crises/resolve - Resolve a crisis if one was generated"""
        print("\n🎯 Testing POST /api/crises/resolve...")
        
        if not self.generated_crisis:
            self.log_test("POST /api/crises/resolve", True, "No crisis to resolve (skipped)")
            return True
        
        crisis = self.generated_crisis
        options = crisis.get("options", [])
        
        if not options:
            self.log_test("POST /api/crises/resolve", False, "No options available in generated crisis")
            return False
        
        # Choose the first available option
        chosen_option = options[0]
        option_id = chosen_option.get("id")
        crisis_id = crisis.get("id")
        
        try:
            response = self.session.post(f"{BASE_URL}/crises/resolve", json={
                "crisis_id": crisis_id,
                "option_id": option_id
            })
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["success", "option_chosen", "cost", "xp_gained", "message", "new_money"]
                
                if all(field in data for field in required_fields):
                    if data.get("success") is True:
                        cost = data.get("cost", 0)
                        xp_gained = data.get("xp_gained", 0)
                        risk_triggered = data.get("risk_triggered", False)
                        
                        self.log_test("POST /api/crises/resolve", True, 
                                    f"Crisis resolved successfully. Cost: R$ {cost}, XP: +{xp_gained}, Risk triggered: {risk_triggered}")
                        return True
                    else:
                        self.log_test("POST /api/crises/resolve", False, 
                                    "Success field is False", data)
                        return False
                else:
                    self.log_test("POST /api/crises/resolve", False, 
                                f"Missing required fields. Expected: {required_fields}", data)
                    return False
            else:
                self.log_test("POST /api/crises/resolve", False, 
                            f"HTTP {response.status_code}", response.json())
                return False
                
        except Exception as e:
            self.log_test("POST /api/crises/resolve", False, f"Exception: {str(e)}")
            return False
    
    def test_get_crises_history(self):
        """Test GET /api/crises/history - Get resolved crises history"""
        print("\n📚 Testing GET /api/crises/history...")
        
        try:
            response = self.session.get(f"{BASE_URL}/crises/history")
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["crises", "count"]
                
                if all(field in data for field in required_fields):
                    crises = data.get("crises", [])
                    count = data.get("count", 0)
                    
                    if len(crises) == count:
                        if count > 0:
                            # Validate crisis structure in history
                            first_crisis = crises[0]
                            history_fields = ["id", "type", "title", "status", "chosen_option", "cost_applied", "xp_gained"]
                            
                            if all(field in first_crisis for field in history_fields):
                                self.log_test("GET /api/crises/history", True, 
                                            f"Crisis history retrieved: {count} crises")
                                return True
                            else:
                                self.log_test("GET /api/crises/history", False, 
                                            f"Invalid crisis structure in history", data)
                                return False
                        else:
                            self.log_test("GET /api/crises/history", True, 
                                        "Crisis history retrieved: 0 crises (empty)")
                            return True
                    else:
                        self.log_test("GET /api/crises/history", False, 
                                    f"Count mismatch: crises length={len(crises)}, count={count}", data)
                        return False
                else:
                    self.log_test("GET /api/crises/history", False, 
                                f"Missing required fields. Expected: {required_fields}", data)
                    return False
            else:
                self.log_test("GET /api/crises/history", False, 
                            f"HTTP {response.status_code}", response.json())
                return False
                
        except Exception as e:
            self.log_test("GET /api/crises/history", False, f"Exception: {str(e)}")
            return False
    
    def test_invalid_crisis_resolve(self):
        """Test error handling with invalid crisis_id"""
        print("\n🚫 Testing error handling (invalid crisis_id)...")
        
        try:
            response = self.session.post(f"{BASE_URL}/crises/resolve", json={
                "crisis_id": "invalid-crisis-id-12345",
                "option_id": "any_option"
            })
            
            if response.status_code == 404:
                data = response.json()
                self.log_test("Error handling (invalid crisis_id)", True, 
                            f"Correctly returned 404 for invalid crisis_id")
                return True
            else:
                self.log_test("Error handling (invalid crisis_id)", False, 
                            f"Expected 404 but got {response.status_code}", response.json())
                return False
                
        except Exception as e:
            self.log_test("Error handling (invalid crisis_id)", False, f"Exception: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run the complete test suite"""
        print("🚀 Starting Life Phases & Crises System Testing...")
        print(f"🌐 Backend URL: {BASE_URL}")
        print(f"👤 Test User: {TEST_EMAIL}")
        
        # Login first
        if not self.login():
            print("❌ Login failed. Cannot proceed with tests.")
            return False
        
        # Test sequence as specified in the review request
        tests = [
            self.test_get_current_phase,        # 1. GET /api/phases/current
            self.test_get_all_phases,           # 2. GET /api/phases/all
            self.test_get_active_crises_empty,  # 3. GET /api/crises/active (empty)
            self.test_check_crisis_generation,  # 4. POST /api/crises/check
            self.test_resolve_crisis,           # 5. POST /api/crises/resolve (if crisis generated)
            self.test_get_crises_history,       # 6. GET /api/crises/history
            self.test_invalid_crisis_resolve,   # 7. Error handling
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            if test():
                passed += 1
            time.sleep(0.5)  # Small delay between tests
        
        # Summary
        print(f"\n📊 TEST SUMMARY")
        print(f"{'='*50}")
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        if passed == total:
            print("🎉 ALL TESTS PASSED! Life Phases & Crises System is working correctly.")
            return True
        else:
            print("⚠️  Some tests failed. Check the details above.")
            return False

if __name__ == "__main__":
    tester = BizRealmsPhasesTester()
    success = tester.run_all_tests()
    
    # Print detailed results for debugging
    print(f"\n📋 DETAILED TEST RESULTS")
    print(f"{'='*50}")
    for result in tester.test_results:
        status = "✅" if result["success"] else "❌"
        print(f"{status} {result['test']}: {result['details']}")
    
    exit(0 if success else 1)