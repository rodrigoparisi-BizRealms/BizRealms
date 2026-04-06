#!/usr/bin/env python3
"""
BizRealms Backend Testing - New Features
Testing: Certification Ranking Bonus & Ad-Free Subscription
"""

import requests
import json
import sys
from datetime import datetime

# Backend URL from environment
BACKEND_URL = "https://career-mogul-1.preview.emergentagent.com/api"

# Test credentials
TEST_EMAIL = "teste@businessempire.com"
TEST_PASSWORD = "teste123"

class BizRealmsAPITester:
    def __init__(self):
        self.token = None
        self.user_id = None
        self.session = requests.Session()
        
    def login(self):
        """Login and get JWT token"""
        print("🔐 Testing login...")
        response = self.session.post(f"{BACKEND_URL}/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        if response.status_code == 200:
            data = response.json()
            self.token = data.get('token')  # Changed from 'access_token' to 'token'
            self.user_id = data.get('user', {}).get('id')
            self.session.headers.update({'Authorization': f'Bearer {self.token}'})
            print(f"✅ Login successful! User ID: {self.user_id}")
            print(f"   Token: {self.token[:50]}...")
            return True
        else:
            print(f"❌ Login failed: {response.status_code} - {response.text}")
            return False
    
    def test_rankings_certification_bonus(self):
        """Test GET /api/rankings for certification bonus fields"""
        print("\n📊 Testing Rankings with Certification Bonus...")
        
        response = self.session.get(f"{BACKEND_URL}/rankings")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Rankings endpoint working - {data.get('total_players', 0)} players")
            
            # Check if rankings have the new certification bonus fields
            rankings = data.get('rankings', [])
            if rankings:
                first_player = rankings[0]
                required_fields = ['cert_bonus_pct', 'cert_bonus_value', 'cert_count', 'base_net_worth']
                missing_fields = []
                
                for field in required_fields:
                    if field not in first_player:
                        missing_fields.append(field)
                
                if missing_fields:
                    print(f"❌ Missing certification bonus fields: {missing_fields}")
                    return False
                else:
                    print(f"✅ All certification bonus fields present:")
                    print(f"   - cert_bonus_pct: {first_player['cert_bonus_pct']}%")
                    print(f"   - cert_bonus_value: R$ {first_player['cert_bonus_value']}")
                    print(f"   - cert_count: {first_player['cert_count']}")
                    print(f"   - base_net_worth: R$ {first_player['base_net_worth']}")
                    print(f"   - total_net_worth: R$ {first_player['total_net_worth']}")
                    
                    # Verify calculation: total = base + cert_bonus_value
                    expected_total = first_player['base_net_worth'] + first_player['cert_bonus_value']
                    actual_total = first_player['total_net_worth']
                    if abs(expected_total - actual_total) < 0.01:  # Allow for rounding
                        print(f"✅ Certification bonus calculation correct")
                        return True
                    else:
                        print(f"❌ Certification bonus calculation error: expected {expected_total}, got {actual_total}")
                        return False
            else:
                print("❌ No rankings data found")
                return False
        else:
            print(f"❌ Rankings endpoint failed: {response.status_code} - {response.text}")
            return False
    
    def test_store_items_ad_free(self):
        """Test GET /api/store/items for ad_free_monthly item"""
        print("\n🛒 Testing Store Items for Ad-Free Subscription...")
        
        response = self.session.get(f"{BACKEND_URL}/store/items")
        
        if response.status_code == 200:
            items = response.json()
            print(f"✅ Store items endpoint working - {len(items)} items found")
            
            # Look for ad_free_monthly item
            ad_free_item = None
            for item in items:
                if item.get('id') == 'ad_free_monthly':
                    ad_free_item = item
                    break
            
            if ad_free_item:
                print(f"✅ Found ad_free_monthly item:")
                print(f"   - Name: {ad_free_item.get('name')}")
                print(f"   - Category: {ad_free_item.get('category')}")
                print(f"   - Price: R$ {ad_free_item.get('price_brl')}")
                print(f"   - Is Subscription: {ad_free_item.get('is_subscription')}")
                
                # Verify required properties
                if (ad_free_item.get('category') == 'premium' and 
                    ad_free_item.get('price_brl') == 9.90 and 
                    ad_free_item.get('is_subscription') == True):
                    print(f"✅ Ad-free item properties correct")
                    return True
                else:
                    print(f"❌ Ad-free item properties incorrect")
                    print(f"   Expected: category='premium', price=9.90, is_subscription=True")
                    print(f"   Actual: category='{ad_free_item.get('category')}', price={ad_free_item.get('price_brl')}, is_subscription={ad_free_item.get('is_subscription')}")
                    return False
            else:
                print("❌ ad_free_monthly item not found in store")
                return False
        else:
            print(f"❌ Store items endpoint failed: {response.status_code} - {response.text}")
            return False
    
    def test_subscription_status_inactive(self):
        """Test GET /api/store/subscription-status for inactive user"""
        print("\n📱 Testing Subscription Status (should be inactive)...")
        
        response = self.session.get(f"{BACKEND_URL}/store/subscription-status")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Subscription status endpoint working")
            print(f"   - ad_free: {data.get('ad_free')}")
            print(f"   - expires_at: {data.get('expires_at')}")
            print(f"   - days_remaining: {data.get('days_remaining')}")
            
            # Verify inactive subscription
            if (data.get('ad_free') == False and 
                data.get('expires_at') is None and 
                data.get('days_remaining') == 0):
                print(f"✅ Subscription correctly shows as inactive")
                return True
            else:
                print(f"❌ Subscription status incorrect for inactive user")
                return False
        else:
            print(f"❌ Subscription status endpoint failed: {response.status_code} - {response.text}")
            return False
    
    def test_buy_ad_free_subscription(self):
        """Test POST /api/store/purchase with ad_free_monthly"""
        print("\n💳 Testing Ad-Free Subscription Purchase...")
        
        response = self.session.post(f"{BACKEND_URL}/store/purchase", json={
            "item_id": "ad_free_monthly",
            "payment_method": "credit_card"
        })
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Ad-free subscription purchase successful!")
            print(f"   - Message: {data.get('message')}")
            print(f"   - Transaction ID: {data.get('transaction_id')}")
            print(f"   - Mock Payment: {data.get('mock_payment')}")
            return True
        else:
            print(f"❌ Ad-free subscription purchase failed: {response.status_code} - {response.text}")
            return False
    
    def test_subscription_status_active(self):
        """Test GET /api/store/subscription-status after purchase (should be active)"""
        print("\n📱 Testing Subscription Status (should be active after purchase)...")
        
        response = self.session.get(f"{BACKEND_URL}/store/subscription-status")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Subscription status endpoint working")
            print(f"   - ad_free: {data.get('ad_free')}")
            print(f"   - expires_at: {data.get('expires_at')}")
            print(f"   - days_remaining: {data.get('days_remaining')}")
            
            # Verify active subscription
            if (data.get('ad_free') == True and 
                data.get('expires_at') is not None and 
                data.get('days_remaining') > 25):  # Should be ~30 days
                print(f"✅ Subscription correctly shows as active with ~30 days remaining")
                return True
            else:
                print(f"❌ Subscription status incorrect after purchase")
                return False
        else:
            print(f"❌ Subscription status endpoint failed: {response.status_code} - {response.text}")
            return False
    
    def run_all_tests(self):
        """Run all tests in sequence"""
        print("🚀 Starting BizRealms Backend Testing - New Features")
        print("=" * 60)
        
        if not self.login():
            return False
        
        tests = [
            ("Rankings Certification Bonus", self.test_rankings_certification_bonus),
            ("Store Items Ad-Free", self.test_store_items_ad_free),
            ("Subscription Status (Inactive)", self.test_subscription_status_inactive),
            ("Buy Ad-Free Subscription", self.test_buy_ad_free_subscription),
            ("Subscription Status (Active)", self.test_subscription_status_active),
        ]
        
        results = []
        for test_name, test_func in tests:
            try:
                result = test_func()
                results.append((test_name, result))
            except Exception as e:
                print(f"❌ {test_name} failed with exception: {e}")
                results.append((test_name, False))
        
        # Summary
        print("\n" + "=" * 60)
        print("📋 TEST SUMMARY")
        print("=" * 60)
        
        passed = 0
        failed = 0
        
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} - {test_name}")
            if result:
                passed += 1
            else:
                failed += 1
        
        print(f"\nTotal: {passed + failed} tests")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        
        if failed == 0:
            print("\n🎉 ALL TESTS PASSED!")
            return True
        else:
            print(f"\n⚠️  {failed} TEST(S) FAILED")
            return False

if __name__ == "__main__":
    tester = BizRealmsAPITester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)