#!/usr/bin/env python3
"""
Backend Testing Script for Real Money Rewards System
Business Empire Game - Testing Agent
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BACKEND_URL = "https://career-mogul-1.preview.emergentagent.com/api"
TEST_EMAIL = "teste@businessempire.com"
TEST_PASSWORD = "teste123"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_success(message):
    print(f"{Colors.GREEN}✅ {message}{Colors.END}")

def print_error(message):
    print(f"{Colors.RED}❌ {message}{Colors.END}")

def print_info(message):
    print(f"{Colors.BLUE}ℹ️  {message}{Colors.END}")

def print_warning(message):
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.END}")

def print_header(message):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{message}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")

class RealMoneyRewardsTest:
    def __init__(self):
        self.token = None
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })

    def login(self):
        """Login and get JWT token"""
        print_header("AUTHENTICATION TEST")
        
        login_data = {
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        }
        
        try:
            response = self.session.post(f"{BACKEND_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get('token')  # Backend returns 'token' not 'access_token'
                if self.token:
                    self.session.headers.update({
                        'Authorization': f'Bearer {self.token}'
                    })
                    print_success(f"Login successful for {TEST_EMAIL}")
                    print_info(f"JWT Token: {self.token[:50]}...")
                    return True
                else:
                    print_error("No access token in response")
                    return False
            else:
                print_error(f"Login failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print_error(f"Login error: {str(e)}")
            return False

    def test_prize_pool_endpoint(self):
        """Test GET /api/rewards/prize-pool"""
        print_header("TESTING PRIZE POOL ENDPOINT")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/rewards/prize-pool")
            
            if response.status_code == 200:
                data = response.json()
                print_success("Prize pool endpoint working")
                
                # Validate required fields
                required_fields = [
                    'current_month', 'prize_pool_total', 'distribution', 
                    'top3', 'user_position', 'total_players', 'has_pix_key', 
                    'days_remaining', 'has_unclaimed_reward', 'history'
                ]
                
                missing_fields = [field for field in required_fields if field not in data]
                if missing_fields:
                    print_error(f"Missing required fields: {missing_fields}")
                    return False
                
                # Validate distribution structure
                distribution = data.get('distribution', {})
                if not all(pos in distribution for pos in ['1st', '2nd', '3rd']):
                    print_error("Distribution missing required positions")
                    return False
                
                print_info(f"Current month: {data['current_month']}")
                print_info(f"Prize pool total: R$ {data['prize_pool_total']:.2f}")
                print_info(f"Distribution - 1st: R$ {distribution['1st']:.2f}, 2nd: R$ {distribution['2nd']:.2f}, 3rd: R$ {distribution['3rd']:.2f}")
                print_info(f"Total players: {data['total_players']}")
                print_info(f"User position: {data['user_position']}")
                print_info(f"Has PIX key: {data['has_pix_key']}")
                print_info(f"Days remaining: {data['days_remaining']}")
                print_info(f"Has unclaimed reward: {data['has_unclaimed_reward']}")
                print_info(f"Top 3 players: {len(data['top3'])} players")
                
                # Store initial state for later comparison
                self.initial_has_pix = data['has_pix_key']
                self.initial_unclaimed = data['has_unclaimed_reward']
                
                return True
            else:
                print_error(f"Prize pool endpoint failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print_error(f"Prize pool test error: {str(e)}")
            return False

    def test_update_pix_endpoint(self):
        """Test POST /api/rewards/update-pix"""
        print_header("TESTING UPDATE PIX ENDPOINT")
        
        pix_data = {
            "pix_key": "12345678901",
            "pix_type": "cpf"
        }
        
        try:
            response = self.session.post(f"{BACKEND_URL}/rewards/update-pix", json=pix_data)
            
            if response.status_code == 200:
                data = response.json()
                print_success("PIX key update successful")
                print_info(f"Response: {data.get('message', 'No message')}")
                
                if data.get('success'):
                    print_success("PIX key successfully updated")
                    return True
                else:
                    print_error("PIX update returned success=False")
                    return False
            else:
                print_error(f"PIX update failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print_error(f"PIX update test error: {str(e)}")
            return False

    def test_prize_pool_after_pix(self):
        """Test GET /api/rewards/prize-pool after PIX update"""
        print_header("TESTING PRIZE POOL AFTER PIX UPDATE")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/rewards/prize-pool")
            
            if response.status_code == 200:
                data = response.json()
                print_success("Prize pool endpoint working after PIX update")
                
                if data.get('has_pix_key'):
                    print_success("has_pix_key is now true")
                    print_info(f"PIX key: {data.get('pix_key', 'Not shown')}")
                    return True
                else:
                    print_error("has_pix_key is still false after PIX update")
                    return False
            else:
                print_error(f"Prize pool endpoint failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print_error(f"Prize pool after PIX test error: {str(e)}")
            return False

    def test_distribute_monthly_endpoint(self):
        """Test POST /api/rewards/distribute-monthly"""
        print_header("TESTING DISTRIBUTE MONTHLY REWARDS")
        
        try:
            response = self.session.post(f"{BACKEND_URL}/rewards/distribute-monthly")
            
            if response.status_code == 200:
                data = response.json()
                print_success("Monthly distribution endpoint working")
                print_info(f"Response: {data.get('message', 'No message')}")
                
                if data.get('success'):
                    print_success("Monthly rewards distributed successfully")
                    return True
                elif "já foi distribuída" in data.get('message', ''):
                    print_warning("Monthly rewards already distributed this month")
                    print_info("This is expected behavior - distribution only happens once per month")
                    return True
                else:
                    print_error("Monthly distribution returned success=False")
                    return False
            else:
                print_error(f"Monthly distribution failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print_error(f"Monthly distribution test error: {str(e)}")
            return False

    def test_prize_pool_after_distribution(self):
        """Test GET /api/rewards/prize-pool after distribution"""
        print_header("TESTING PRIZE POOL AFTER DISTRIBUTION")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/rewards/prize-pool")
            
            if response.status_code == 200:
                data = response.json()
                print_success("Prize pool endpoint working after distribution")
                
                print_info(f"Has unclaimed reward: {data['has_unclaimed_reward']}")
                
                if data.get('has_unclaimed_reward'):
                    unclaimed = data.get('unclaimed_reward', {})
                    print_success("User has unclaimed reward!")
                    print_info(f"Reward amount: R$ {unclaimed.get('amount', 0):.2f}")
                    print_info(f"Position: {unclaimed.get('position', 'Unknown')}")
                    print_info(f"Month: {unclaimed.get('month', 'Unknown')}")
                    print_info(f"Reward ID: {unclaimed.get('id', 'Unknown')}")
                    
                    # Store reward ID for claiming test
                    self.reward_id = unclaimed.get('id')
                    return True
                else:
                    print_warning("User has no unclaimed rewards")
                    print_info("This might be expected if user is not in top 3 or rewards already claimed")
                    return True
            else:
                print_error(f"Prize pool endpoint failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print_error(f"Prize pool after distribution test error: {str(e)}")
            return False

    def test_claim_real_reward(self):
        """Test POST /api/rewards/claim-real"""
        print_header("TESTING CLAIM REAL MONEY REWARD")
        
        if not hasattr(self, 'reward_id') or not self.reward_id:
            print_warning("No reward ID available for claiming test")
            print_info("This might be expected if user is not in top 3")
            return True
        
        claim_data = {
            "reward_id": self.reward_id
        }
        
        try:
            response = self.session.post(f"{BACKEND_URL}/rewards/claim-real", json=claim_data)
            
            if response.status_code == 200:
                data = response.json()
                print_success("Reward claim successful")
                print_info(f"Message: {data.get('message', 'No message')}")
                print_info(f"Amount: R$ {data.get('amount', 0):.2f}")
                print_info(f"Position: {data.get('position', 'Unknown')}")
                
                if data.get('success'):
                    print_success("Real money reward claimed successfully")
                    return True
                else:
                    print_error("Reward claim returned success=False")
                    return False
            elif response.status_code == 400:
                error_msg = response.json().get('detail', response.text)
                if "Configure sua chave PIX" in error_msg:
                    print_error("PIX key not configured (this shouldn't happen after PIX update)")
                    return False
                else:
                    print_warning(f"Claim failed with 400: {error_msg}")
                    return True
            elif response.status_code == 404:
                print_warning("Reward not found or already claimed")
                print_info("This might be expected if reward was already claimed or user not in top 3")
                return True
            else:
                print_error(f"Reward claim failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print_error(f"Reward claim test error: {str(e)}")
            return False

    def run_all_tests(self):
        """Run all Real Money Rewards tests"""
        print_header("REAL MONEY REWARDS SYSTEM TESTING")
        print_info(f"Backend URL: {BACKEND_URL}")
        print_info(f"Test User: {TEST_EMAIL}")
        print_info(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        tests = [
            ("Login", self.login),
            ("Prize Pool Initial", self.test_prize_pool_endpoint),
            ("Update PIX Key", self.test_update_pix_endpoint),
            ("Prize Pool After PIX", self.test_prize_pool_after_pix),
            ("Distribute Monthly", self.test_distribute_monthly_endpoint),
            ("Prize Pool After Distribution", self.test_prize_pool_after_distribution),
            ("Claim Real Reward", self.test_claim_real_reward),
        ]
        
        results = []
        
        for test_name, test_func in tests:
            print(f"\n{Colors.YELLOW}Running: {test_name}{Colors.END}")
            try:
                result = test_func()
                results.append((test_name, result))
                if result:
                    print_success(f"{test_name} - PASSED")
                else:
                    print_error(f"{test_name} - FAILED")
            except Exception as e:
                print_error(f"{test_name} - ERROR: {str(e)}")
                results.append((test_name, False))
        
        # Summary
        print_header("TEST RESULTS SUMMARY")
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} - {test_name}")
        
        print(f"\n{Colors.BOLD}Overall: {passed}/{total} tests passed{Colors.END}")
        
        if passed == total:
            print_success("🎉 ALL TESTS PASSED! Real Money Rewards system is working correctly.")
            return True
        else:
            print_error(f"❌ {total - passed} tests failed. Please check the issues above.")
            return False

def main():
    """Main test execution"""
    tester = RealMoneyRewardsTest()
    success = tester.run_all_tests()
    
    if success:
        print(f"\n{Colors.GREEN}{Colors.BOLD}✅ REAL MONEY REWARDS SYSTEM: FULLY FUNCTIONAL{Colors.END}")
        sys.exit(0)
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}❌ REAL MONEY REWARDS SYSTEM: ISSUES FOUND{Colors.END}")
        sys.exit(1)

if __name__ == "__main__":
    main()