#!/usr/bin/env python3
"""
BizRealms Backend Testing - New Endpoints
Testing the 4 new endpoints:
1. POST /api/user/reset-account
2. POST /api/store/double-daily  
3. POST /api/user/watch-ad
4. POST /api/companies/create (bug fix verification)
"""

import requests
import json
import time
from datetime import datetime

# Backend URL from frontend/.env
BASE_URL = "https://career-mogul-1.preview.emergentagent.com/api"

# Test credentials
MAIN_USER = {"email": "teste@businessempire.com", "password": "teste123"}
ALT_USER = {"email": "test_jobs@businessempire.com", "password": "test123"}

class BizRealmsAPITester:
    def __init__(self):
        self.session = requests.Session()
        self.main_token = None
        self.alt_token = None
        self.temp_user_token = None
        self.temp_user_email = None
        
    def log(self, message):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
        
    def login(self, credentials):
        """Login and return JWT token"""
        self.log(f"🔐 Logging in as {credentials['email']}")
        response = self.session.post(f"{BASE_URL}/auth/login", json=credentials)
        
        if response.status_code == 200:
            data = response.json()
            token = data.get('token') or data.get('access_token')  # Try both field names
            if token:
                self.log(f"✅ Login successful, token: {token[:20]}...")
                return token
            else:
                self.log(f"❌ Login response missing token: {data}")
                return None
        else:
            self.log(f"❌ Login failed: {response.status_code} - {response.text}")
            return None
            
    def create_temp_user(self):
        """Create a temporary user for reset testing"""
        import uuid
        temp_email = f"temp_test_{uuid.uuid4().hex[:8]}@test.com"
        temp_password = "temp123"
        
        self.log(f"👤 Creating temporary user: {temp_email}")
        
        user_data = {
            "email": temp_email,
            "password": temp_password,
            "name": "Temp Test User"
        }
        
        response = self.session.post(f"{BASE_URL}/auth/register", json=user_data)
        
        if response.status_code in [200, 201]:  # Accept both 200 and 201
            self.log("✅ Temporary user created successfully")
            # Login with temp user
            login_response = self.session.post(f"{BASE_URL}/auth/login", json={
                "email": temp_email,
                "password": temp_password
            })
            
            if login_response.status_code == 200:
                token = login_response.json().get('token') or login_response.json().get('access_token')
                self.temp_user_token = token
                self.temp_user_email = temp_email
                self.log(f"✅ Temp user logged in, token: {token[:20]}...")
                return token
            else:
                self.log(f"❌ Failed to login temp user: {login_response.text}")
                return None
        else:
            self.log(f"❌ Failed to create temp user: {response.status_code} - {response.text}")
            return None
    
    def make_request(self, method, endpoint, token, data=None):
        """Make authenticated API request"""
        headers = {"Authorization": f"Bearer {token}"}
        url = f"{BASE_URL}{endpoint}"
        
        if method.upper() == "GET":
            response = self.session.get(url, headers=headers)
        elif method.upper() == "POST":
            response = self.session.post(url, headers=headers, json=data)
        elif method.upper() == "PUT":
            response = self.session.put(url, headers=headers, json=data)
        else:
            raise ValueError(f"Unsupported method: {method}")
            
        return response
    
    def test_daily_reward_flow(self, token):
        """Test the complete daily reward flow: check status → claim → check doubled status → double it"""
        self.log("\n🎁 Testing Daily Reward Flow")
        
        # 1. Check daily reward status
        self.log("1️⃣ Checking daily reward status...")
        response = self.make_request("GET", "/store/daily-reward-status", token)
        
        if response.status_code == 200:
            status = response.json()
            self.log(f"✅ Daily reward status: available={status.get('available')}, already_claimed={status.get('already_claimed')}, reward_amount={status.get('reward_amount')}, doubled={status.get('doubled')}")
            
            # 2. Claim daily reward if available
            if status.get('available'):
                self.log("2️⃣ Claiming daily reward...")
                claim_response = self.make_request("POST", "/store/daily-reward", token)
                
                if claim_response.status_code == 200:
                    claim_data = claim_response.json()
                    self.log(f"✅ Daily reward claimed: {claim_data.get('message')}, amount={claim_data.get('amount')}, new_balance={claim_data.get('new_balance')}")
                    
                    # 3. Check doubled status after claiming
                    self.log("3️⃣ Checking doubled status after claiming...")
                    status_response = self.make_request("GET", "/store/daily-reward-status", token)
                    
                    if status_response.status_code == 200:
                        new_status = status_response.json()
                        self.log(f"✅ Updated status: available={new_status.get('available')}, doubled={new_status.get('doubled')}")
                        
                        # 4. Double the daily reward if not already doubled
                        if not new_status.get('doubled'):
                            self.log("4️⃣ Doubling daily reward...")
                            double_response = self.make_request("POST", "/store/double-daily", token)
                            
                            if double_response.status_code == 200:
                                double_data = double_response.json()
                                self.log(f"✅ Daily reward doubled: {double_data.get('message')}, bonus_amount={double_data.get('bonus_amount')}, new_balance={double_data.get('new_balance')}")
                                return True
                            else:
                                self.log(f"❌ Failed to double daily reward: {double_response.status_code} - {double_response.text}")
                                return False
                        else:
                            self.log("ℹ️ Daily reward already doubled today")
                            return True
                    else:
                        self.log(f"❌ Failed to check status after claiming: {status_response.status_code} - {status_response.text}")
                        return False
                else:
                    self.log(f"❌ Failed to claim daily reward: {claim_response.status_code} - {claim_response.text}")
                    return False
            else:
                self.log("ℹ️ Daily reward already claimed today")
                
                # Try to double it anyway
                self.log("4️⃣ Attempting to double already claimed reward...")
                double_response = self.make_request("POST", "/store/double-daily", token)
                
                if double_response.status_code == 200:
                    double_data = double_response.json()
                    self.log(f"✅ Daily reward doubled: {double_data.get('message')}")
                    return True
                elif double_response.status_code == 400:
                    self.log(f"ℹ️ Expected error (already doubled): {double_response.json().get('detail')}")
                    return True
                else:
                    self.log(f"❌ Unexpected error doubling reward: {double_response.status_code} - {double_response.text}")
                    return False
        else:
            self.log(f"❌ Failed to check daily reward status: {response.status_code} - {response.text}")
            return False
    
    def test_watch_ad_tracking(self, token):
        """Test the watch ad tracking endpoint"""
        self.log("\n📺 Testing Watch Ad Tracking")
        
        # Get initial ad count
        self.log("1️⃣ Getting user profile to check initial ad count...")
        profile_response = self.make_request("GET", "/user/me", token)
        
        if profile_response.status_code == 200:
            profile = profile_response.json()
            initial_ads = profile.get('ads_watched_today', 0)
            self.log(f"✅ Initial ads watched today: {initial_ads}")
        else:
            self.log(f"❌ Failed to get user profile: {profile_response.status_code} - {profile_response.text}")
            initial_ads = 0
        
        # Watch an ad
        self.log("2️⃣ Watching an ad...")
        watch_response = self.make_request("POST", "/user/watch-ad", token)
        
        if watch_response.status_code == 200:
            watch_data = watch_response.json()
            self.log(f"✅ Ad watched: {watch_data.get('message')}, ads_watched_today={watch_data.get('ads_watched_today')}")
            
            # Verify the count increased
            expected_count = initial_ads + 1
            actual_count = watch_data.get('ads_watched_today')
            
            if actual_count == expected_count:
                self.log(f"✅ Ad count correctly incremented: {initial_ads} → {actual_count}")
                return True
            else:
                self.log(f"❌ Ad count mismatch: expected {expected_count}, got {actual_count}")
                return False
        else:
            self.log(f"❌ Failed to watch ad: {watch_response.status_code} - {watch_response.text}")
            return False
    
    def test_company_creation(self, token):
        """Test company creation (bug fix verification)"""
        self.log("\n🏢 Testing Company Creation (Bug Fix)")
        
        # Get user balance first
        self.log("1️⃣ Getting user balance...")
        profile_response = self.make_request("GET", "/user/me", token)
        
        if profile_response.status_code == 200:
            profile = profile_response.json()
            initial_money = profile.get('money', 0)
            self.log(f"✅ Initial balance: R$ {initial_money:,.2f}")
            
            if initial_money < 5000:
                self.log("⚠️ Insufficient funds for company creation (need R$ 5,000)")
                return False
        else:
            self.log(f"❌ Failed to get user profile: {profile_response.status_code} - {profile_response.text}")
            return False
        
        # Create a company
        company_data = {
            "name": "Test Company API",
            "segment": "restaurante"
        }
        
        self.log(f"2️⃣ Creating company: {company_data}")
        create_response = self.make_request("POST", "/companies/create", token, company_data)
        
        if create_response.status_code == 200:
            create_data = create_response.json()
            self.log(f"✅ Company created: {create_data.get('message')}")
            self.log(f"   Company details: {create_data.get('company')}")
            self.log(f"   New balance: R$ {create_data.get('new_balance'):,.2f}")
            
            # Verify balance decreased by 5000
            expected_balance = initial_money - 5000
            actual_balance = create_data.get('new_balance')
            
            if abs(actual_balance - expected_balance) < 0.01:
                self.log(f"✅ Balance correctly decreased by R$ 5,000")
                return True
            else:
                self.log(f"❌ Balance mismatch: expected {expected_balance}, got {actual_balance}")
                return False
        else:
            self.log(f"❌ Failed to create company: {create_response.status_code} - {create_response.text}")
            return False
    
    def test_account_reset(self, token):
        """Test account reset endpoint (CRITICAL: Only use with temp user)"""
        self.log("\n🔄 Testing Account Reset (TEMP USER ONLY)")
        
        # First, add some data to the temp user to make reset meaningful
        self.log("1️⃣ Adding some data to temp user before reset...")
        
        # Add education
        education_data = {
            "institution": "Test University",
            "degree": "Test Degree",
            "field": "administração",
            "level": 2,
            "start_date": "2020-01-01",
            "end_date": "2022-12-31"
        }
        
        edu_response = self.make_request("POST", "/user/education", token, education_data)
        if edu_response.status_code == 200:
            self.log("✅ Added test education")
        else:
            self.log(f"⚠️ Failed to add education: {edu_response.text}")
        
        # Get user profile before reset
        self.log("2️⃣ Getting user profile before reset...")
        before_response = self.make_request("GET", "/user/me", token)
        
        if before_response.status_code == 200:
            before_profile = before_response.json()
            self.log(f"✅ Before reset - Money: R$ {before_profile.get('money', 0):,.2f}, Level: {before_profile.get('level', 1)}, XP: {before_profile.get('experience_points', 0)}")
            self.log(f"   Education count: {len(before_profile.get('education', []))}")
        else:
            self.log(f"❌ Failed to get profile before reset: {before_response.status_code} - {before_response.text}")
            return False
        
        # Perform reset
        self.log("3️⃣ Performing account reset...")
        reset_response = self.make_request("POST", "/user/reset-account", token)
        
        if reset_response.status_code == 200:
            reset_data = reset_response.json()
            self.log(f"✅ Account reset: {reset_data.get('message')}")
            
            # Get user profile after reset
            self.log("4️⃣ Getting user profile after reset...")
            after_response = self.make_request("GET", "/user/me", token)
            
            if after_response.status_code == 200:
                after_profile = after_response.json()
                self.log(f"✅ After reset - Money: R$ {after_profile.get('money', 0):,.2f}, Level: {after_profile.get('level', 1)}, XP: {after_profile.get('experience_points', 0)}")
                self.log(f"   Education count: {len(after_profile.get('education', []))}")
                
                # Verify reset worked
                if (after_profile.get('money') == 1000 and 
                    after_profile.get('level') == 1 and 
                    after_profile.get('experience_points') == 0 and
                    len(after_profile.get('education', [])) == 0):
                    self.log("✅ Account reset successful - all game data cleared")
                    return True
                else:
                    self.log("❌ Account reset incomplete - some data not cleared")
                    return False
            else:
                self.log(f"❌ Failed to get profile after reset: {after_response.status_code} - {after_response.text}")
                return False
        else:
            self.log(f"❌ Failed to reset account: {reset_response.status_code} - {reset_response.text}")
            return False
    
    def run_all_tests(self):
        """Run all tests"""
        self.log("🚀 Starting BizRealms Backend Testing - New Endpoints")
        self.log("=" * 60)
        
        # Login with main user
        self.main_token = self.login(MAIN_USER)
        if not self.main_token:
            self.log("❌ Failed to login with main user, aborting tests")
            return
        
        # Login with alt user  
        self.alt_token = self.login(ALT_USER)
        if not self.alt_token:
            self.log("❌ Failed to login with alt user, aborting tests")
            return
        
        # Create temp user for reset test
        self.temp_user_token = self.create_temp_user()
        if not self.temp_user_token:
            self.log("❌ Failed to create temp user, skipping reset test")
        
        results = {}
        
        # Test 1: Daily reward flow (with main user)
        results['daily_reward_flow'] = self.test_daily_reward_flow(self.main_token)
        
        # Test 2: Watch ad tracking (with alt user)
        results['watch_ad_tracking'] = self.test_watch_ad_tracking(self.alt_token)
        
        # Test 3: Company creation (with main user)
        results['company_creation'] = self.test_company_creation(self.main_token)
        
        # Test 4: Account reset (with temp user only)
        if self.temp_user_token:
            results['account_reset'] = self.test_account_reset(self.temp_user_token)
        else:
            results['account_reset'] = False
            self.log("⚠️ Skipped account reset test - no temp user")
        
        # Summary
        self.log("\n" + "=" * 60)
        self.log("📊 TEST RESULTS SUMMARY")
        self.log("=" * 60)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            self.log(f"{test_name.replace('_', ' ').title()}: {status}")
        
        passed = sum(results.values())
        total = len(results)
        self.log(f"\nOverall: {passed}/{total} tests passed")
        
        if passed == total:
            self.log("🎉 ALL TESTS PASSED!")
        else:
            self.log("⚠️ Some tests failed - check logs above")
        
        return results

if __name__ == "__main__":
    tester = BizRealmsAPITester()
    tester.run_all_tests()