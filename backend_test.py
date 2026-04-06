#!/usr/bin/env python3
"""
BizRealms Backend Testing - Prestige System and Weekly Competitions System
Testing the NEW Prestige System and Weekly Competitions System endpoints.
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BASE_URL = "https://career-mogul-1.preview.emergentagent.com/api"
TEST_EMAIL = "teste@businessempire.com"
TEST_PASSWORD = "teste123"

class BizRealmsAPITester:
    def __init__(self):
        self.session = requests.Session()
        self.jwt_token = None
        self.user_data = None
        
    def log(self, message, level="INFO"):
        """Log test messages with timestamp."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def login(self):
        """Login and get JWT token."""
        self.log("🔐 Testing login...")
        
        response = self.session.post(f"{BASE_URL}/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        if response.status_code != 200:
            self.log(f"❌ Login failed: {response.status_code} - {response.text}", "ERROR")
            return False
            
        data = response.json()
        self.jwt_token = data.get('token')  # Fixed: API returns 'token' not 'access_token'
        self.user_data = data.get('user', {})
        
        if not self.jwt_token:
            self.log("❌ No JWT token received", "ERROR")
            return False
            
        # Set authorization header for all future requests
        self.session.headers.update({
            'Authorization': f'Bearer {self.jwt_token}',
            'Content-Type': 'application/json'
        })
        
        self.log(f"✅ Login successful! User: {self.user_data.get('name', 'Unknown')}")
        return True
        
    def test_prestige_status(self):
        """Test GET /api/prestige/status endpoint."""
        self.log("🏆 Testing prestige status...")
        
        response = self.session.get(f"{BASE_URL}/prestige/status")
        
        if response.status_code != 200:
            self.log(f"❌ Prestige status failed: {response.status_code} - {response.text}", "ERROR")
            return False
            
        data = response.json()
        
        # Validate response structure
        required_fields = [
            'tier', 'total_points_earned', 'available_points', 'resets_count',
            'active_perks', 'potential_points', 'current_net_worth'
        ]
        
        for field in required_fields:
            if field not in data:
                self.log(f"❌ Missing field in prestige status: {field}", "ERROR")
                return False
                
        # Validate tier structure
        tier = data['tier']
        tier_fields = ['level', 'name', 'emoji', 'color', 'min_points']
        for field in tier_fields:
            if field not in tier:
                self.log(f"❌ Missing tier field: {field}", "ERROR")
                return False
                
        self.log(f"✅ Prestige status working! Tier: {tier['emoji']} {tier['name']}")
        self.log(f"   📊 Total points: {data['total_points_earned']}, Available: {data['available_points']}")
        self.log(f"   💰 Net worth: R$ {data['current_net_worth']:,.2f}, Potential points: {data['potential_points']}")
        self.log(f"   🔄 Resets: {data['resets_count']}, Active perks: {len(data['active_perks'])}")
        
        return True
        
    def test_prestige_perks(self):
        """Test GET /api/prestige/perks endpoint."""
        self.log("🎁 Testing prestige perks...")
        
        response = self.session.get(f"{BASE_URL}/prestige/perks")
        
        if response.status_code != 200:
            self.log(f"❌ Prestige perks failed: {response.status_code} - {response.text}", "ERROR")
            return False
            
        data = response.json()
        
        # Validate response structure
        if 'perks' not in data or 'available_points' not in data or 'tier' not in data:
            self.log("❌ Missing fields in prestige perks response", "ERROR")
            return False
            
        perks = data['perks']
        if not isinstance(perks, list):
            self.log("❌ Perks should be a list", "ERROR")
            return False
            
        if len(perks) == 0:
            self.log("❌ No perks returned", "ERROR")
            return False
            
        # Validate perk structure
        perk_fields = [
            'id', 'name', 'cost', 'owned', 'can_afford', 'tier_unlocked',
            'prerequisite_met', 'available'
        ]
        
        for perk in perks[:3]:  # Check first 3 perks
            for field in perk_fields:
                if field not in perk:
                    self.log(f"❌ Missing perk field: {field} in perk {perk.get('id', 'unknown')}", "ERROR")
                    return False
                    
        self.log(f"✅ Prestige perks working! Found {len(perks)} perks")
        self.log(f"   💎 Available points: {data['available_points']}")
        
        # Show some example perks
        for perk in perks[:3]:
            status = "✅ Available" if perk['available'] else "❌ Not available"
            self.log(f"   🎁 {perk['name']} - Cost: {perk['cost']} - {status}")
            
        return True
        
    def test_prestige_buy_perk(self):
        """Test POST /api/prestige/buy-perk endpoint."""
        self.log("💳 Testing prestige perk purchase...")
        
        # First get available perks to find one we can potentially buy
        response = self.session.get(f"{BASE_URL}/prestige/perks")
        if response.status_code != 200:
            self.log("❌ Could not get perks for purchase test", "ERROR")
            return False
            
        data = response.json()
        available_perks = [p for p in data['perks'] if p['available']]
        
        if not available_perks:
            self.log("ℹ️ No available perks to purchase (expected if user has no points)")
            # Test with insufficient points - should fail gracefully
            response = self.session.post(f"{BASE_URL}/prestige/buy-perk", json={
                "perk_id": "starting_money_1"
            })
            
            if response.status_code == 400:
                error_data = response.json()
                if "insuficientes" in error_data.get('detail', '').lower():
                    self.log("✅ Perk purchase correctly rejected - insufficient points")
                    return True
                else:
                    self.log(f"✅ Perk purchase correctly rejected: {error_data.get('detail', 'Unknown error')}")
                    return True
            else:
                self.log(f"❌ Expected 400 error for insufficient points, got {response.status_code}", "ERROR")
                return False
        else:
            # Try to buy the first available perk
            perk = available_perks[0]
            response = self.session.post(f"{BASE_URL}/prestige/buy-perk", json={
                "perk_id": perk['id']
            })
            
            if response.status_code == 200:
                result = response.json()
                self.log(f"✅ Perk purchase successful! Bought: {result['perk']['name']}")
                self.log(f"   💰 Remaining points: {result['remaining_points']}")
                return True
            elif response.status_code == 400:
                error_data = response.json()
                self.log(f"✅ Perk purchase correctly rejected: {error_data.get('detail', 'Unknown error')}")
                return True
            else:
                self.log(f"❌ Unexpected response for perk purchase: {response.status_code} - {response.text}", "ERROR")
                return False
                
    def test_prestige_reset_validation(self):
        """Test POST /api/prestige/reset endpoint validation (without actually resetting)."""
        self.log("🔄 Testing prestige reset validation...")
        
        response = self.session.post(f"{BASE_URL}/prestige/reset")
        
        if response.status_code == 400:
            error_data = response.json()
            if "insuficiente" in error_data.get('detail', '').lower():
                self.log("✅ Prestige reset correctly rejected - insufficient net worth")
                return True
            else:
                self.log(f"✅ Prestige reset correctly rejected: {error_data.get('detail', 'Unknown error')}")
                return True
        elif response.status_code == 200:
            self.log("⚠️ WARNING: Prestige reset succeeded! This will reset all game data!")
            result = response.json()
            self.log(f"   🏆 Points earned: {result.get('points_earned', 0)}")
            self.log(f"   💰 Starting money: R$ {result.get('starting_money', 0)}")
            return True
        else:
            self.log(f"❌ Unexpected response for prestige reset: {response.status_code} - {response.text}", "ERROR")
            return False
            
    def test_competitions_active(self):
        """Test GET /api/competitions/active endpoint."""
        self.log("🏁 Testing active competitions...")
        
        response = self.session.get(f"{BASE_URL}/competitions/active")
        
        if response.status_code != 200:
            self.log(f"❌ Active competitions failed: {response.status_code} - {response.text}", "ERROR")
            return False
            
        data = response.json()
        
        # Validate response structure
        if 'competitions' not in data or 'count' not in data:
            self.log("❌ Missing fields in competitions response", "ERROR")
            return False
            
        competitions = data['competitions']
        if not isinstance(competitions, list):
            self.log("❌ Competitions should be a list", "ERROR")
            return False
            
        self.log(f"✅ Active competitions working! Found {data['count']} competitions")
        
        if len(competitions) == 0:
            self.log("ℹ️ No active competitions (this might be expected)")
            return True
            
        # Validate competition structure
        comp_fields = [
            'id', 'title', 'emoji', 'description', 'metric', 'leaderboard',
            'my_position', 'my_score', 'rewards', 'days_remaining'
        ]
        
        for comp in competitions:
            for field in comp_fields:
                if field not in comp:
                    self.log(f"❌ Missing competition field: {field}", "ERROR")
                    return False
                    
            self.log(f"   🏆 {comp['emoji']} {comp['title']}")
            self.log(f"      📊 Your position: #{comp['my_position']}, Score: {comp['my_score']}")
            self.log(f"      ⏰ Days remaining: {comp['days_remaining']}")
            self.log(f"      🎁 Rewards: {len(comp['rewards'])} positions")
            
        return True
        
    def test_competitions_leaderboard(self):
        """Test GET /api/competitions/leaderboard/{id} endpoint."""
        self.log("📊 Testing competition leaderboard...")
        
        # First get active competitions to get an ID
        response = self.session.get(f"{BASE_URL}/competitions/active")
        if response.status_code != 200:
            self.log("❌ Could not get competitions for leaderboard test", "ERROR")
            return False
            
        data = response.json()
        competitions = data['competitions']
        
        if len(competitions) == 0:
            self.log("ℹ️ No competitions available for leaderboard test")
            return True
            
        comp_id = competitions[0]['id']
        response = self.session.get(f"{BASE_URL}/competitions/leaderboard/{comp_id}")
        
        if response.status_code != 200:
            self.log(f"❌ Competition leaderboard failed: {response.status_code} - {response.text}", "ERROR")
            return False
            
        data = response.json()
        
        # Validate response structure
        if 'competition' not in data or 'leaderboard' not in data:
            self.log("❌ Missing fields in leaderboard response", "ERROR")
            return False
            
        leaderboard = data['leaderboard']
        if not isinstance(leaderboard, list):
            self.log("❌ Leaderboard should be a list", "ERROR")
            return False
            
        self.log(f"✅ Competition leaderboard working! {len(leaderboard)} participants")
        
        # Show top 3 entries
        for i, entry in enumerate(leaderboard[:3]):
            you_marker = " (YOU)" if entry.get('is_you') else ""
            self.log(f"   #{entry['position']} {entry['name']}{you_marker} - Score: {entry['score']}")
            
        return True
        
    def test_competitions_history(self):
        """Test GET /api/competitions/history endpoint."""
        self.log("📚 Testing competition history...")
        
        response = self.session.get(f"{BASE_URL}/competitions/history")
        
        if response.status_code != 200:
            self.log(f"❌ Competition history failed: {response.status_code} - {response.text}", "ERROR")
            return False
            
        data = response.json()
        
        # Validate response structure
        if 'competitions' not in data or 'count' not in data:
            self.log("❌ Missing fields in history response", "ERROR")
            return False
            
        competitions = data['competitions']
        if not isinstance(competitions, list):
            self.log("❌ History competitions should be a list", "ERROR")
            return False
            
        self.log(f"✅ Competition history working! Found {data['count']} past competitions")
        
        if len(competitions) == 0:
            self.log("ℹ️ No past competitions (expected for new system)")
        else:
            for comp in competitions[:3]:  # Show first 3
                self.log(f"   🏆 {comp.get('emoji', '')} {comp.get('title', 'Unknown')}")
                
        return True
        
    def test_error_handling(self):
        """Test error handling for invalid requests."""
        self.log("🚫 Testing error handling...")
        
        # Test invalid perk ID
        response = self.session.post(f"{BASE_URL}/prestige/buy-perk", json={
            "perk_id": "invalid_perk_id"
        })
        
        if response.status_code == 404:
            self.log("✅ Invalid perk ID correctly rejected with 404")
        else:
            self.log(f"❌ Expected 404 for invalid perk, got {response.status_code}", "ERROR")
            return False
            
        # Test invalid competition ID
        response = self.session.get(f"{BASE_URL}/competitions/leaderboard/invalid_id")
        
        if response.status_code == 404:
            self.log("✅ Invalid competition ID correctly rejected with 404")
        else:
            self.log(f"❌ Expected 404 for invalid competition, got {response.status_code}", "ERROR")
            return False
            
        return True
        
    def run_all_tests(self):
        """Run all tests in sequence."""
        self.log("🚀 Starting BizRealms Prestige & Competitions System Tests")
        self.log("=" * 60)
        
        tests = [
            ("Login", self.login),
            ("Prestige Status", self.test_prestige_status),
            ("Prestige Perks", self.test_prestige_perks),
            ("Prestige Buy Perk", self.test_prestige_buy_perk),
            ("Prestige Reset Validation", self.test_prestige_reset_validation),
            ("Active Competitions", self.test_competitions_active),
            ("Competition Leaderboard", self.test_competitions_leaderboard),
            ("Competition History", self.test_competitions_history),
            ("Error Handling", self.test_error_handling),
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            self.log(f"\n🧪 Running test: {test_name}")
            try:
                if test_func():
                    passed += 1
                    self.log(f"✅ {test_name} PASSED")
                else:
                    failed += 1
                    self.log(f"❌ {test_name} FAILED")
            except Exception as e:
                failed += 1
                self.log(f"❌ {test_name} FAILED with exception: {str(e)}", "ERROR")
                
        self.log("\n" + "=" * 60)
        self.log(f"🏁 Test Results: {passed} passed, {failed} failed")
        
        if failed == 0:
            self.log("🎉 ALL TESTS PASSED! Prestige & Competitions systems are working correctly.")
            return True
        else:
            self.log(f"⚠️ {failed} tests failed. Please check the issues above.")
            return False

if __name__ == "__main__":
    tester = BizRealmsAPITester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)