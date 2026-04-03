#!/usr/bin/env python3
"""
Backend Testing Script for BizRealms Game App
Tests the newly implemented endpoints: Notifications, Achievements, Stripe Checkout, and Payments History
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
        self.token = None
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    def login(self):
        """Login and get JWT token"""
        self.log("🔐 Attempting login...")
        
        login_data = {
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get('token')
                if self.token:
                    self.session.headers.update({'Authorization': f'Bearer {self.token}'})
                    self.log("✅ Login successful")
                    return True
                else:
                    self.log("❌ Login failed: No token in response", "ERROR")
                    return False
            else:
                self.log(f"❌ Login failed: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Login error: {str(e)}", "ERROR")
            return False
    
    def test_notifications_system(self):
        """Test notifications endpoints"""
        self.log("\n📢 TESTING NOTIFICATIONS SYSTEM")
        
        # Test GET /api/notifications
        self.log("Testing GET /api/notifications...")
        try:
            response = self.session.get(f"{BASE_URL}/notifications")
            
            if response.status_code == 200:
                data = response.json()
                notifications = data.get('notifications', [])
                unread_count = data.get('unread_count', 0)
                
                self.log(f"✅ GET /api/notifications successful")
                self.log(f"   📊 Total notifications: {len(notifications)}")
                self.log(f"   📊 Unread count: {unread_count}")
                
                # Show first few notifications
                for i, notif in enumerate(notifications[:3]):
                    self.log(f"   📝 Notification {i+1}: {notif.get('title', 'No title')} - {notif.get('message', 'No message')}")
                
                # Test marking notification as read if we have any
                if notifications:
                    first_notif_id = notifications[0].get('id')
                    if first_notif_id:
                        self.log(f"Testing POST /api/notifications/read with ID: {first_notif_id}")
                        read_response = self.session.post(f"{BASE_URL}/notifications/read", 
                                                        json={"notification_id": first_notif_id})
                        
                        if read_response.status_code == 200:
                            self.log("✅ Mark single notification as read successful")
                        else:
                            self.log(f"❌ Mark notification as read failed: {read_response.status_code} - {read_response.text}")
                
                # Test mark all as read
                self.log("Testing POST /api/notifications/read (mark all)...")
                read_all_response = self.session.post(f"{BASE_URL}/notifications/read", 
                                                    json={"notification_id": "all"})
                
                if read_all_response.status_code == 200:
                    self.log("✅ Mark all notifications as read successful")
                else:
                    self.log(f"❌ Mark all notifications as read failed: {read_all_response.status_code} - {read_all_response.text}")
                
                return True
                
            else:
                self.log(f"❌ GET /api/notifications failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Notifications test error: {str(e)}", "ERROR")
            return False
    
    def test_achievements_system(self):
        """Test achievements endpoints"""
        self.log("\n🏆 TESTING ACHIEVEMENTS SYSTEM")
        
        # Test GET /api/achievements
        self.log("Testing GET /api/achievements...")
        try:
            response = self.session.get(f"{BASE_URL}/achievements")
            
            if response.status_code == 200:
                data = response.json()
                achievements = data.get('achievements', [])
                total = data.get('total', 0)
                unlocked = data.get('unlocked', 0)
                
                self.log(f"✅ GET /api/achievements successful")
                self.log(f"   📊 Total achievements: {total}")
                self.log(f"   📊 Unlocked achievements: {unlocked}")
                
                # Show achievements status
                unlocked_count = 0
                for ach in achievements:
                    status = "🔓" if ach.get('unlocked') else "🔒"
                    self.log(f"   {status} {ach.get('id', 'unknown')}: {ach.get('icon', '?')} (+{ach.get('xp', 0)} XP, +R$ {ach.get('money', 0)})")
                    if ach.get('unlocked'):
                        unlocked_count += 1
                
                # Test POST /api/achievements/check
                self.log("Testing POST /api/achievements/check...")
                check_response = self.session.post(f"{BASE_URL}/achievements/check")
                
                if check_response.status_code == 200:
                    check_data = check_response.json()
                    new_unlocks = check_data.get('new_unlocks', [])
                    count = check_data.get('count', 0)
                    
                    self.log(f"✅ POST /api/achievements/check successful")
                    self.log(f"   📊 New unlocks: {count}")
                    
                    if new_unlocks:
                        for unlock in new_unlocks:
                            self.log(f"   🎉 New achievement unlocked: {unlock}")
                    else:
                        self.log("   ℹ️ No new achievements unlocked")
                    
                    return True
                else:
                    self.log(f"❌ POST /api/achievements/check failed: {check_response.status_code} - {check_response.text}")
                    return False
                
            else:
                self.log(f"❌ GET /api/achievements failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Achievements test error: {str(e)}", "ERROR")
            return False
    
    def test_stripe_checkout_system(self):
        """Test Stripe checkout endpoints"""
        self.log("\n💳 TESTING STRIPE CHECKOUT SYSTEM")
        
        # Test POST /api/payments/create-checkout-session
        self.log("Testing POST /api/payments/create-checkout-session...")
        try:
            checkout_data = {"item_id": "pack_starter"}  # Using money_starter as mentioned in review request
            response = self.session.post(f"{BASE_URL}/payments/create-checkout-session", json=checkout_data)
            
            if response.status_code == 200:
                data = response.json()
                session_id = data.get('session_id')
                checkout_url = data.get('checkout_url')
                
                self.log(f"✅ POST /api/payments/create-checkout-session successful")
                self.log(f"   📊 Session ID: {session_id}")
                self.log(f"   📊 Checkout URL: {checkout_url}")
                
                # Test POST /api/payments/check-session with the session ID
                self.log("Testing POST /api/payments/check-session...")
                check_data = {"session_id": session_id}
                check_response = self.session.post(f"{BASE_URL}/payments/check-session", json=check_data)
                
                if check_response.status_code == 200:
                    check_result = check_response.json()
                    status = check_result.get('status')
                    message = check_result.get('message')
                    
                    self.log(f"✅ POST /api/payments/check-session successful")
                    self.log(f"   📊 Status: {status}")
                    self.log(f"   📊 Message: {message}")
                    
                    return True
                else:
                    self.log(f"❌ POST /api/payments/check-session failed: {check_response.status_code} - {check_response.text}")
                    return False
                
            elif response.status_code == 404:
                self.log(f"❌ Item 'pack_starter' not found. Trying 'money_starter'...")
                # Try with money_starter as mentioned in review request
                checkout_data = {"item_id": "money_starter"}
                response = self.session.post(f"{BASE_URL}/payments/create-checkout-session", json=checkout_data)
                
                if response.status_code == 200:
                    data = response.json()
                    session_id = data.get('session_id')
                    checkout_url = data.get('checkout_url')
                    
                    self.log(f"✅ POST /api/payments/create-checkout-session successful with money_starter")
                    self.log(f"   📊 Session ID: {session_id}")
                    self.log(f"   📊 Checkout URL: {checkout_url}")
                    return True
                else:
                    self.log(f"❌ POST /api/payments/create-checkout-session failed: {response.status_code} - {response.text}")
                    return False
            else:
                self.log(f"❌ POST /api/payments/create-checkout-session failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Stripe checkout test error: {str(e)}", "ERROR")
            return False
    
    def test_payments_history(self):
        """Test payments history endpoint"""
        self.log("\n💰 TESTING PAYMENTS HISTORY")
        
        # Test GET /api/payments/history
        self.log("Testing GET /api/payments/history...")
        try:
            response = self.session.get(f"{BASE_URL}/payments/history")
            
            if response.status_code == 200:
                data = response.json()
                purchases = data.get('purchases', [])
                
                self.log(f"✅ GET /api/payments/history successful")
                self.log(f"   📊 Total purchases: {len(purchases)}")
                
                # Show recent purchases
                for i, purchase in enumerate(purchases[:5]):
                    item_name = purchase.get('item_name', 'Unknown item')
                    price = purchase.get('price_brl', 0)
                    payment_method = purchase.get('payment_method', 'unknown')
                    status = purchase.get('status', 'unknown')
                    created_at = purchase.get('created_at', 'unknown')
                    
                    self.log(f"   💳 Purchase {i+1}: {item_name} - R$ {price} ({payment_method}) - {status} - {created_at}")
                
                return True
                
            else:
                self.log(f"❌ GET /api/payments/history failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Payments history test error: {str(e)}", "ERROR")
            return False
    
    def test_check_session_with_invalid_id(self):
        """Test check-session endpoint with invalid session ID"""
        self.log("\n🔍 TESTING CHECK-SESSION WITH INVALID ID")
        
        self.log("Testing POST /api/payments/check-session with invalid session_id...")
        try:
            check_data = {"session_id": "some_test_id"}
            response = self.session.post(f"{BASE_URL}/payments/check-session", json=check_data)
            
            # This should handle the error gracefully
            if response.status_code in [200, 400, 404]:
                if response.status_code == 200:
                    data = response.json()
                    self.log(f"✅ POST /api/payments/check-session handled invalid ID gracefully")
                    self.log(f"   📊 Response: {data}")
                else:
                    self.log(f"✅ POST /api/payments/check-session properly rejected invalid ID: {response.status_code}")
                    self.log(f"   📊 Error: {response.text}")
                return True
            else:
                self.log(f"❌ POST /api/payments/check-session failed unexpectedly: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Check session invalid ID test error: {str(e)}", "ERROR")
            return False
    
    def run_all_tests(self):
        """Run all tests"""
        self.log("🚀 STARTING BIZREALMS BACKEND API TESTING")
        self.log(f"🌐 Base URL: {BASE_URL}")
        self.log(f"👤 Test User: {TEST_EMAIL}")
        
        # Login first
        if not self.login():
            self.log("❌ Cannot proceed without authentication", "ERROR")
            return False
        
        # Run all tests
        results = {
            "notifications": self.test_notifications_system(),
            "achievements": self.test_achievements_system(),
            "stripe_checkout": self.test_stripe_checkout_system(),
            "payments_history": self.test_payments_history(),
            "check_session_invalid": self.test_check_session_with_invalid_id()
        }
        
        # Summary
        self.log("\n📊 TEST SUMMARY")
        self.log("=" * 50)
        
        passed = 0
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            self.log(f"{status} {test_name.replace('_', ' ').title()}")
            if result:
                passed += 1
        
        self.log("=" * 50)
        self.log(f"📈 OVERALL RESULT: {passed}/{total} tests passed")
        
        if passed == total:
            self.log("🎉 ALL TESTS PASSED!")
            return True
        else:
            self.log("⚠️ SOME TESTS FAILED!")
            return False

def main():
    """Main function"""
    tester = BizRealmsAPITester()
    success = tester.run_all_tests()
    
    if success:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()