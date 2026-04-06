#!/usr/bin/env python3
"""
BizRealms Backend Testing - AI Dynamic Events System
Comprehensive testing of the new AI Dynamic Events System endpoints.
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "https://career-mogul-1.preview.emergentagent.com/api"
TEST_EMAIL = "teste@businessempire.com"
TEST_PASSWORD = "teste123"

class BizRealmsEventsTester:
    def __init__(self):
        self.session = requests.Session()
        self.jwt_token = None
        self.user_data = None
        self.test_results = []
        
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
    
    def test_get_active_event_empty(self):
        """Test GET /api/events/active when no event exists"""
        print("\n📋 Testing GET /api/events/active (empty state)...")
        
        try:
            response = self.session.get(f"{BASE_URL}/events/active")
            
            if response.status_code == 200:
                data = response.json()
                expected_fields = ["event", "has_event", "cooldown_remaining"]
                
                if all(field in data for field in expected_fields):
                    if data["event"] is None and data["has_event"] is False:
                        self.log_test("GET /api/events/active (empty)", True, 
                                    f"Correct empty state: event=null, has_event=false, cooldown={data['cooldown_remaining']}")
                        return True
                    else:
                        self.log_test("GET /api/events/active (empty)", False, 
                                    f"Unexpected state: event={data['event']}, has_event={data['has_event']}", data)
                        return False
                else:
                    self.log_test("GET /api/events/active (empty)", False, 
                                f"Missing required fields. Expected: {expected_fields}", data)
                    return False
            else:
                self.log_test("GET /api/events/active (empty)", False, 
                            f"HTTP {response.status_code}", response.json())
                return False
                
        except Exception as e:
            self.log_test("GET /api/events/active (empty)", False, f"Exception: {str(e)}")
            return False
    
    def test_generate_event(self):
        """Test POST /api/events/generate"""
        print("\n🎲 Testing POST /api/events/generate...")
        
        try:
            response = self.session.post(f"{BASE_URL}/events/generate")
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if event was generated or if there's a cooldown/existing event
                if data.get("generated") is True and "event" in data:
                    event = data["event"]
                    required_fields = ["id", "type", "title", "description", "choices", "emoji", "color"]
                    
                    if all(field in event for field in required_fields):
                        choices = event.get("choices", [])
                        if len(choices) >= 2:  # Should have at least 2 choices
                            # Validate choice structure
                            choice_valid = True
                            for choice in choices:
                                if not all(field in choice for field in ["id", "text", "consequences"]):
                                    choice_valid = False
                                    break
                                consequences = choice.get("consequences", {})
                                if not isinstance(consequences, dict):
                                    choice_valid = False
                                    break
                            
                            if choice_valid:
                                self.log_test("POST /api/events/generate", True, 
                                            f"Event generated successfully. Type: {event['type']}, Title: {event['title']}, Choices: {len(choices)}")
                                self.generated_event = event  # Store for later tests
                                return True
                            else:
                                self.log_test("POST /api/events/generate", False, 
                                            "Invalid choice structure", data)
                                return False
                        else:
                            self.log_test("POST /api/events/generate", False, 
                                        f"Insufficient choices: {len(choices)}", data)
                            return False
                    else:
                        self.log_test("POST /api/events/generate", False, 
                                    f"Missing required event fields. Expected: {required_fields}", data)
                        return False
                elif data.get("generated") is False:
                    # Event not generated due to cooldown or existing event
                    message = data.get("message", "Unknown reason")
                    self.log_test("POST /api/events/generate", True, 
                                f"Event not generated (expected): {message}")
                    return True
                else:
                    self.log_test("POST /api/events/generate", False, 
                                "Unexpected response structure", data)
                    return False
            else:
                self.log_test("POST /api/events/generate", False, 
                            f"HTTP {response.status_code}", response.json())
                return False
                
        except Exception as e:
            self.log_test("POST /api/events/generate", False, f"Exception: {str(e)}")
            return False
    
    def test_get_active_event_with_event(self):
        """Test GET /api/events/active when event exists"""
        print("\n📋 Testing GET /api/events/active (with event)...")
        
        try:
            response = self.session.get(f"{BASE_URL}/events/active")
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("has_event") is True and data.get("event") is not None:
                    event = data["event"]
                    required_fields = ["id", "type", "title", "description", "choices"]
                    
                    if all(field in event for field in required_fields):
                        self.log_test("GET /api/events/active (with event)", True, 
                                    f"Active event found: {event['title']}")
                        self.active_event = event  # Store for choice test
                        return True
                    else:
                        self.log_test("GET /api/events/active (with event)", False, 
                                    f"Missing required fields in event", data)
                        return False
                else:
                    self.log_test("GET /api/events/active (with event)", False, 
                                f"Expected active event but got: has_event={data.get('has_event')}", data)
                    return False
            else:
                self.log_test("GET /api/events/active (with event)", False, 
                            f"HTTP {response.status_code}", response.json())
                return False
                
        except Exception as e:
            self.log_test("GET /api/events/active (with event)", False, f"Exception: {str(e)}")
            return False
    
    def test_choose_event_option(self):
        """Test POST /api/events/choose"""
        print("\n🎯 Testing POST /api/events/choose...")
        
        if not hasattr(self, 'active_event'):
            self.log_test("POST /api/events/choose", False, "No active event available for choice test")
            return False
        
        event = self.active_event
        choices = event.get("choices", [])
        
        if not choices:
            self.log_test("POST /api/events/choose", False, "No choices available in active event")
            return False
        
        # Choose the first available option
        chosen_choice = choices[0]
        choice_id = chosen_choice.get("id")
        event_id = event.get("id")
        
        try:
            response = self.session.post(f"{BASE_URL}/events/choose", json={
                "event_id": event_id,
                "choice_id": choice_id
            })
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["success", "choice", "consequences"]
                
                if all(field in data for field in required_fields):
                    if data.get("success") is True:
                        consequences = data.get("consequences", {})
                        money_change = consequences.get("money", 0)
                        xp_change = consequences.get("xp", 0)
                        
                        self.log_test("POST /api/events/choose", True, 
                                    f"Choice made successfully. Money: {money_change:+}, XP: {xp_change:+}")
                        return True
                    else:
                        self.log_test("POST /api/events/choose", False, 
                                    "Success field is False", data)
                        return False
                else:
                    self.log_test("POST /api/events/choose", False, 
                                f"Missing required fields. Expected: {required_fields}", data)
                    return False
            else:
                self.log_test("POST /api/events/choose", False, 
                            f"HTTP {response.status_code}", response.json())
                return False
                
        except Exception as e:
            self.log_test("POST /api/events/choose", False, f"Exception: {str(e)}")
            return False
    
    def test_get_event_history(self):
        """Test GET /api/events/history"""
        print("\n📚 Testing GET /api/events/history...")
        
        try:
            response = self.session.get(f"{BASE_URL}/events/history")
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["events", "count"]
                
                if all(field in data for field in required_fields):
                    events = data.get("events", [])
                    count = data.get("count", 0)
                    
                    if len(events) == count:
                        if count > 0:
                            # Validate event structure in history
                            first_event = events[0]
                            history_fields = ["id", "type", "title", "resolved", "chosen_option", "applied_consequences"]
                            
                            if all(field in first_event for field in history_fields):
                                self.log_test("GET /api/events/history", True, 
                                            f"Event history retrieved: {count} events")
                                return True
                            else:
                                self.log_test("GET /api/events/history", False, 
                                            f"Invalid event structure in history", data)
                                return False
                        else:
                            self.log_test("GET /api/events/history", True, 
                                        "Event history retrieved: 0 events (empty)")
                            return True
                    else:
                        self.log_test("GET /api/events/history", False, 
                                    f"Count mismatch: events length={len(events)}, count={count}", data)
                        return False
                else:
                    self.log_test("GET /api/events/history", False, 
                                f"Missing required fields. Expected: {required_fields}", data)
                    return False
            else:
                self.log_test("GET /api/events/history", False, 
                            f"HTTP {response.status_code}", response.json())
                return False
                
        except Exception as e:
            self.log_test("GET /api/events/history", False, f"Exception: {str(e)}")
            return False
    
    def test_cooldown_mechanism(self):
        """Test cooldown mechanism by trying to generate another event immediately"""
        print("\n⏰ Testing cooldown mechanism...")
        
        try:
            response = self.session.post(f"{BASE_URL}/events/generate")
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("generated") is False:
                    message = data.get("message", "")
                    if "cooldown" in message.lower() or "aguarde" in message.lower():
                        self.log_test("Cooldown mechanism", True, 
                                    f"Cooldown working correctly: {message}")
                        return True
                    else:
                        self.log_test("Cooldown mechanism", False, 
                                    f"Unexpected message: {message}", data)
                        return False
                else:
                    self.log_test("Cooldown mechanism", False, 
                                "Expected cooldown but event was generated", data)
                    return False
            else:
                self.log_test("Cooldown mechanism", False, 
                            f"HTTP {response.status_code}", response.json())
                return False
                
        except Exception as e:
            self.log_test("Cooldown mechanism", False, f"Exception: {str(e)}")
            return False
    
    def test_invalid_event_choice(self):
        """Test error handling with invalid event_id"""
        print("\n🚫 Testing error handling (invalid event_id)...")
        
        try:
            response = self.session.post(f"{BASE_URL}/events/choose", json={
                "event_id": "invalid-event-id-12345",
                "choice_id": "any_choice"
            })
            
            if response.status_code == 404:
                data = response.json()
                self.log_test("Error handling (invalid event_id)", True, 
                            f"Correctly returned 404 for invalid event_id")
                return True
            else:
                self.log_test("Error handling (invalid event_id)", False, 
                            f"Expected 404 but got {response.status_code}", response.json())
                return False
                
        except Exception as e:
            self.log_test("Error handling (invalid event_id)", False, f"Exception: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run the complete test suite"""
        print("🚀 Starting AI Dynamic Events System Testing...")
        print(f"🌐 Backend URL: {BASE_URL}")
        print(f"👤 Test User: {TEST_EMAIL}")
        
        # Login first
        if not self.login():
            print("❌ Login failed. Cannot proceed with tests.")
            return False
        
        # Test sequence as specified in the review request
        tests = [
            self.test_get_active_event_empty,      # 1. Check for active event (should be empty)
            self.test_generate_event,              # 2. Generate new event
            self.test_get_active_event_with_event, # 3. Check for active event (should have event)
            self.test_choose_event_option,         # 4. Make a choice
            self.test_get_event_history,           # 5. Check history
            self.test_cooldown_mechanism,          # 6. Test cooldown
            self.test_invalid_event_choice,        # 7. Test error handling
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
            print("🎉 ALL TESTS PASSED! AI Dynamic Events System is working correctly.")
            return True
        else:
            print("⚠️  Some tests failed. Check the details above.")
            return False

if __name__ == "__main__":
    tester = BizRealmsEventsTester()
    success = tester.run_all_tests()
    
    # Print detailed results for debugging
    print(f"\n📋 DETAILED TEST RESULTS")
    print(f"{'='*50}")
    for result in tester.test_results:
        status = "✅" if result["success"] else "❌"
        print(f"{status} {result['test']}: {result['details']}")
    
    exit(0 if success else 1)