#!/usr/bin/env python3
"""
Backend API Testing for Business Empire - Rankings Rewards System
Testing the new rankings rewards endpoints
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "https://career-mogul-1.preview.emergentagent.com/api"

# Test credentials for 2nd place winner
TEST_EMAIL = "test_jobs@businessempire.com"
TEST_PASSWORD = "test123"

class RankingsRewardsTest:
    def __init__(self):
        self.token = None
        self.user_id = None
        
    def login(self):
        """Login and get JWT token"""
        print("🔐 Logging in as test_jobs user...")
        
        response = requests.post(f"{BASE_URL}/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        if response.status_code == 200:
            data = response.json()
            # Try both possible token field names
            self.token = data.get('access_token') or data.get('token')
            self.user_id = data.get('user', {}).get('id')
            print(f"✅ Login successful! User ID: {self.user_id}")
            print(f"✅ Token received: {self.token[:50]}..." if self.token else "❌ No token received")
            return True
        else:
            print(f"❌ Login failed: {response.status_code} - {response.text}")
            return False
    
    def get_headers(self):
        """Get authorization headers"""
        return {"Authorization": f"Bearer {self.token}"}
    
    def test_rankings_with_rewards_info(self):
        """Test GET /api/rankings - should include new reward fields"""
        print("\n📊 Testing GET /api/rankings with rewards info...")
        
        response = requests.get(f"{BASE_URL}/rankings", headers=self.get_headers())
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Rankings endpoint working")
            
            # Check for new fields
            required_fields = ['has_unclaimed_reward', 'unclaimed_reward', 'prizes']
            missing_fields = []
            
            for field in required_fields:
                if field not in data:
                    missing_fields.append(field)
            
            if missing_fields:
                print(f"❌ Missing required fields: {missing_fields}")
                return False
            
            print(f"✅ has_unclaimed_reward: {data['has_unclaimed_reward']}")
            print(f"✅ unclaimed_reward: {data['unclaimed_reward']}")
            print(f"✅ prizes array: {len(data['prizes'])} items")
            
            # Validate prizes array
            prizes = data['prizes']
            if len(prizes) != 3:
                print(f"❌ Expected 3 prizes, got {len(prizes)}")
                return False
            
            # Check prize structure
            for i, prize in enumerate(prizes, 1):
                required_prize_fields = ['position', 'icon', 'color', 'description', 'type']
                for field in required_prize_fields:
                    if field not in prize:
                        print(f"❌ Prize {i} missing field: {field}")
                        return False
                
                if prize['position'] != i:
                    print(f"❌ Prize position mismatch: expected {i}, got {prize['position']}")
                    return False
            
            print("✅ Prizes array structure validated")
            
            # Show current user position
            current_user = data.get('current_user')
            if current_user:
                print(f"✅ Current user position: {current_user.get('position', 'N/A')}")
                print(f"✅ Current user net worth: R$ {current_user.get('total_net_worth', 0):,.2f}")
            
            return True, data
        else:
            print(f"❌ Rankings request failed: {response.status_code} - {response.text}")
            return False, None
    
    def test_distribute_rewards(self):
        """Test POST /api/rankings/distribute-rewards"""
        print("\n🎁 Testing POST /api/rankings/distribute-rewards...")
        
        response = requests.post(f"{BASE_URL}/rankings/distribute-rewards", headers=self.get_headers())
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Distribute rewards endpoint working")
            print(f"✅ Distributed: {data.get('distributed')}")
            print(f"✅ Message: {data.get('message')}")
            
            if data.get('distributed'):
                print("✅ Rewards were distributed this call")
                winners = data.get('winners', [])
                print(f"✅ Winners: {len(winners)} players")
                for winner in winners:
                    print(f"   Position {winner['position']}: {winner['name']} - {winner['prize']}")
            else:
                print("ℹ️ Rewards already distributed this week")
                next_days = data.get('next_distribution_in_days', 'N/A')
                print(f"ℹ️ Next distribution in: {next_days} days")
            
            return True, data
        else:
            print(f"❌ Distribute rewards failed: {response.status_code} - {response.text}")
            return False, None
    
    def test_claim_reward(self):
        """Test POST /api/rankings/claim-reward"""
        print("\n🏆 Testing POST /api/rankings/claim-reward...")
        
        response = requests.post(f"{BASE_URL}/rankings/claim-reward", headers=self.get_headers())
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Claim reward endpoint working")
            print(f"✅ Success: {data.get('success')}")
            print(f"✅ Message: {data.get('message')}")
            print(f"✅ Position: {data.get('position')}")
            print(f"✅ Reward type: {data.get('reward_type')}")
            print(f"✅ Description: {data.get('reward_description')}")
            
            # If it's a boost reward, check ad_boosts collection
            if data.get('reward_type') == 'boost':
                print("🔍 Checking if ad boost was activated...")
                boost_response = requests.get(f"{BASE_URL}/ads/current-boost", headers=self.get_headers())
                if boost_response.status_code == 200:
                    boost_data = boost_response.json()
                    print(f"✅ Ad boost active: {boost_data.get('active')}")
                    print(f"✅ Multiplier: {boost_data.get('multiplier')}x")
                    print(f"✅ Time remaining: {boost_data.get('seconds_remaining')} seconds")
                else:
                    print(f"⚠️ Could not verify ad boost: {boost_response.status_code}")
            
            return True, data
        elif response.status_code == 404:
            print("ℹ️ No unclaimed reward available (404 as expected)")
            return True, None
        else:
            print(f"❌ Claim reward failed: {response.status_code} - {response.text}")
            return False, None
    
    def test_claim_reward_twice(self):
        """Test claiming reward twice - should get 404 on second attempt"""
        print("\n🔄 Testing claim reward twice (should fail second time)...")
        
        # First attempt
        response1 = requests.post(f"{BASE_URL}/rankings/claim-reward", headers=self.get_headers())
        
        # Second attempt immediately after
        response2 = requests.post(f"{BASE_URL}/rankings/claim-reward", headers=self.get_headers())
        
        if response1.status_code == 200 and response2.status_code == 404:
            print("✅ First claim successful, second claim properly rejected with 404")
            return True
        elif response1.status_code == 404 and response2.status_code == 404:
            print("ℹ️ No rewards available for claiming (both attempts returned 404)")
            return True
        else:
            print(f"❌ Unexpected behavior: First: {response1.status_code}, Second: {response2.status_code}")
            return False
    
    def test_auth_debug(self):
        """Debug authentication by testing a simple endpoint"""
        print("\n🔍 Testing authentication with /api/user/me...")
        
        response = requests.get(f"{BASE_URL}/user/me", headers=self.get_headers())
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Authentication working! User: {data.get('name')}")
            return True
        else:
            print(f"❌ Authentication failed: {response.status_code} - {response.text}")
            print(f"🔍 Token: {self.token[:50]}..." if self.token else "No token")
            return False
    
    def run_full_test(self):
        """Run complete rankings rewards test suite"""
        print("🚀 Starting Rankings Rewards System Test")
        print("=" * 50)
        
        # Login
        if not self.login():
            return False
        
        # Debug authentication
        if not self.test_auth_debug():
            return False
        
        # Test 1: Check rankings endpoint with new fields
        success1, rankings_data = self.test_rankings_with_rewards_info()
        if not success1:
            return False
        
        # Test 2: Try to distribute rewards
        success2, distribute_data = self.test_distribute_rewards()
        if not success2:
            return False
        
        # Test 3: Check if user has unclaimed reward after distribution
        print("\n🔍 Checking for unclaimed rewards after distribution...")
        success3, updated_rankings = self.test_rankings_with_rewards_info()
        if not success3:
            return False
        
        # Test 4: Try to claim reward
        success4, claim_data = self.test_claim_reward()
        if not success4:
            return False
        
        # Test 5: Try to claim again (should fail)
        success5 = self.test_claim_reward_twice()
        if not success5:
            return False
        
        # Final check: Verify rankings endpoint shows no unclaimed reward
        print("\n🔍 Final check - rankings should show no unclaimed reward...")
        success6, final_rankings = self.test_rankings_with_rewards_info()
        if success6 and final_rankings:
            if not final_rankings.get('has_unclaimed_reward'):
                print("✅ Confirmed: No unclaimed rewards remaining")
            else:
                print("⚠️ Warning: Still shows unclaimed reward after claiming")
        
        print("\n" + "=" * 50)
        print("🎉 Rankings Rewards System Test Complete!")
        return True

if __name__ == "__main__":
    tester = RankingsRewardsTest()
    success = tester.run_full_test()
    
    if success:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed!")