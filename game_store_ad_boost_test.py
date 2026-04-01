#!/usr/bin/env python3
"""
Business Empire Backend API Test Suite
Focus: Game Store System and Ad Boost (1 Hour Duration) Testing
"""

import requests
import json
import sys
import time
from datetime import datetime

# Configuration
BASE_URL = "https://career-mogul-1.preview.emergentagent.com/api"

# Test users
MAIN_USER = {
    "email": "teste@businessempire.com",
    "password": "teste123",
    "name": "Jogador Teste"
}

JOBS_USER = {
    "email": "test_jobs@businessempire.com", 
    "password": "test123",
    "name": "Test Jobs User"
}

# Global variables
auth_token = None
user_data = None

def log_test(test_name, success, details=""):
    """Log test results"""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status} {test_name}")
    if details:
        print(f"   {details}")
    print()

def make_request(method, endpoint, data=None, headers=None):
    """Make HTTP request with error handling"""
    url = f"{BASE_URL}{endpoint}"
    
    if headers is None:
        headers = {}
    
    if auth_token and 'Authorization' not in headers:
        headers['Authorization'] = f'Bearer {auth_token}'
    
    try:
        if method == 'GET':
            response = requests.get(url, headers=headers, timeout=30)
        elif method == 'POST':
            response = requests.post(url, json=data, headers=headers, timeout=30)
        elif method == 'PUT':
            response = requests.put(url, json=data, headers=headers, timeout=30)
        elif method == 'DELETE':
            response = requests.delete(url, headers=headers, timeout=30)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        return response
    except requests.exceptions.Timeout:
        print(f"❌ Request timeout for {method} {endpoint}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed for {method} {endpoint}: {e}")
        return None

def login_user(user_credentials):
    """Login and get JWT token"""
    global auth_token, user_data
    
    print(f"🔐 Logging in as {user_credentials['email']}...")
    response = make_request('POST', '/auth/login', {
        'email': user_credentials['email'],
        'password': user_credentials['password']
    })
    
    if not response or response.status_code != 200:
        print(f"❌ Login failed: {response.status_code if response else 'No response'}")
        if response:
            print(f"   Response: {response.text}")
        return False
    
    data = response.json()
    auth_token = data.get('token')  # API returns 'token' not 'access_token'
    user_data = data.get('user')
    
    if not auth_token:
        print("❌ No access token received")
        print(f"   Response data: {data}")
        return False
    
    print(f"✅ Login successful! User: {user_data.get('name', 'Unknown')}")
    print(f"   Money: R$ {user_data.get('money', 0):,.2f}")
    print(f"   Level: {user_data.get('level', 1)} (XP: {user_data.get('experience_points', 0):,})")
    print()
    return True

def test_get_store_items():
    """Test 1: GET /api/store/items - List all store items"""
    response = make_request('GET', '/store/items')
    
    if not response or response.status_code != 200:
        log_test("Get Store Items", False, f"Status: {response.status_code if response else 'No response'}")
        return False
    
    try:
        data = response.json()
        if not isinstance(data, list):
            log_test("Get Store Items", False, "Response is not a list")
            return False
        
        if len(data) != 12:
            log_test("Get Store Items", False, f"Expected 12 items, got {len(data)}")
            return False
        
        # Check categories
        categories = set(item.get('category') for item in data)
        expected_categories = {'dinheiro', 'xp', 'ganhos'}
        if categories != expected_categories:
            log_test("Get Store Items", False, f"Expected categories {expected_categories}, got {categories}")
            return False
        
        # Count items per category
        category_counts = {}
        for item in data:
            cat = item.get('category')
            category_counts[cat] = category_counts.get(cat, 0) + 1
        
        log_test("Get Store Items", True, f"12 items found across 3 categories: {category_counts}")
        return True
        
    except json.JSONDecodeError:
        log_test("Get Store Items", False, "Invalid JSON response")
        return False

def test_get_store_items_filtered():
    """Test 2-4: GET /api/store/items with category filters"""
    categories = ['dinheiro', 'xp', 'ganhos']
    expected_counts = {'dinheiro': 5, 'xp': 3, 'ganhos': 4}
    
    all_passed = True
    
    for category in categories:
        response = make_request('GET', f'/store/items?category={category}')
        
        if not response or response.status_code != 200:
            log_test(f"Get Store Items - {category}", False, f"Status: {response.status_code if response else 'No response'}")
            all_passed = False
            continue
        
        try:
            data = response.json()
            if not isinstance(data, list):
                log_test(f"Get Store Items - {category}", False, "Response is not a list")
                all_passed = False
                continue
            
            # Check all items have correct category
            for item in data:
                if item.get('category') != category:
                    log_test(f"Get Store Items - {category}", False, f"Item has wrong category: {item.get('category')}")
                    all_passed = False
                    continue
            
            expected_count = expected_counts[category]
            if len(data) != expected_count:
                log_test(f"Get Store Items - {category}", False, f"Expected {expected_count} items, got {len(data)}")
                all_passed = False
                continue
            
            log_test(f"Get Store Items - {category}", True, f"{len(data)} items found")
            
        except json.JSONDecodeError:
            log_test(f"Get Store Items - {category}", False, "Invalid JSON response")
            all_passed = False
    
    return all_passed

def test_purchase_money_pack():
    """Test 5: POST /api/store/purchase - Buy money pack"""
    global user_data
    
    # Get current money
    initial_money = user_data.get('money', 0)
    
    purchase_data = {
        "item_id": "pack_starter",
        "payment_method": "credit_card"
    }
    
    response = make_request('POST', '/store/purchase', purchase_data)
    
    if not response or response.status_code != 200:
        log_test("Purchase Money Pack", False, f"Status: {response.status_code if response else 'No response'}")
        if response:
            print(f"   Response: {response.text}")
        return False
    
    try:
        data = response.json()
        
        # Check required fields
        required_fields = ['success', 'message', 'item', 'transaction_id', 'payment_method', 'price_brl', 'rewards_applied', 'mock_payment']
        for field in required_fields:
            if field not in data:
                log_test("Purchase Money Pack", False, f"Missing field: {field}")
                return False
        
        if not data.get('success'):
            log_test("Purchase Money Pack", False, "Purchase not successful")
            return False
        
        if not data.get('mock_payment'):
            log_test("Purchase Money Pack", False, "Expected mock_payment flag")
            return False
        
        # Verify user money increased
        profile_response = make_request('GET', '/user/me')
        if profile_response and profile_response.status_code == 200:
            profile_data = profile_response.json()
            new_money = profile_data.get('money', 0)
            expected_increase = 10000  # pack_starter gives 10000
            
            if new_money >= initial_money + expected_increase:
                log_test("Purchase Money Pack", True, f"Money increased from R$ {initial_money:,.2f} to R$ {new_money:,.2f} (+R$ {new_money - initial_money:,.2f})")
                user_data['money'] = new_money
                return True
            else:
                log_test("Purchase Money Pack", False, f"Money not increased correctly. Expected at least +R$ {expected_increase:,.2f}, got +R$ {new_money - initial_money:,.2f}")
                return False
        else:
            log_test("Purchase Money Pack", False, "Could not verify money increase")
            return False
        
    except json.JSONDecodeError:
        log_test("Purchase Money Pack", False, "Invalid JSON response")
        return False

def test_purchase_xp_boost():
    """Test 6: POST /api/store/purchase - Buy XP boost"""
    global user_data
    
    # Get current XP
    initial_xp = user_data.get('experience_points', 0)
    initial_level = user_data.get('level', 1)
    
    purchase_data = {
        "item_id": "xp_small",
        "payment_method": "pix"
    }
    
    response = make_request('POST', '/store/purchase', purchase_data)
    
    if not response or response.status_code != 200:
        log_test("Purchase XP Boost", False, f"Status: {response.status_code if response else 'No response'}")
        if response:
            print(f"   Response: {response.text}")
        return False
    
    try:
        data = response.json()
        
        if not data.get('success'):
            log_test("Purchase XP Boost", False, "Purchase not successful")
            return False
        
        # Verify user XP increased
        profile_response = make_request('GET', '/user/me')
        if profile_response and profile_response.status_code == 200:
            profile_data = profile_response.json()
            new_xp = profile_data.get('experience_points', 0)
            new_level = profile_data.get('level', 1)
            expected_increase = 5000  # xp_small gives 5000 XP
            
            if new_xp >= initial_xp + expected_increase:
                log_test("Purchase XP Boost", True, f"XP increased from {initial_xp:,} to {new_xp:,} (+{new_xp - initial_xp:,}), Level: {initial_level} → {new_level}")
                user_data['experience_points'] = new_xp
                user_data['level'] = new_level
                return True
            else:
                log_test("Purchase XP Boost", False, f"XP not increased correctly. Expected at least +{expected_increase:,}, got +{new_xp - initial_xp:,}")
                return False
        else:
            log_test("Purchase XP Boost", False, "Could not verify XP increase")
            return False
        
    except json.JSONDecodeError:
        log_test("Purchase XP Boost", False, "Invalid JSON response")
        return False

def test_purchase_earnings_boost():
    """Test 7: POST /api/store/purchase - Buy earnings boost"""
    purchase_data = {
        "item_id": "earnings_2x_1h",
        "payment_method": "credit_card"
    }
    
    response = make_request('POST', '/store/purchase', purchase_data)
    
    if not response or response.status_code != 200:
        log_test("Purchase Earnings Boost", False, f"Status: {response.status_code if response else 'No response'}")
        if response:
            print(f"   Response: {response.text}")
        return False
    
    try:
        data = response.json()
        
        if not data.get('success'):
            log_test("Purchase Earnings Boost", False, "Purchase not successful")
            return False
        
        # Check if ad_boosts collection was updated by checking current boost
        boost_response = make_request('GET', '/ads/current-boost')
        if boost_response and boost_response.status_code == 200:
            boost_data = boost_response.json()
            if boost_data.get('active') and boost_data.get('multiplier') >= 2.0:
                log_test("Purchase Earnings Boost", True, f"Earnings boost activated: {boost_data.get('multiplier')}x multiplier, {boost_data.get('seconds_remaining')} seconds remaining")
                return True
            else:
                log_test("Purchase Earnings Boost", False, f"Boost not active or incorrect multiplier: {boost_data}")
                return False
        else:
            log_test("Purchase Earnings Boost", False, "Could not verify boost activation")
            return False
        
    except json.JSONDecodeError:
        log_test("Purchase Earnings Boost", False, "Invalid JSON response")
        return False

def test_get_purchase_history():
    """Test 8: GET /api/store/purchases - Get purchase history"""
    response = make_request('GET', '/store/purchases')
    
    if not response or response.status_code != 200:
        log_test("Get Purchase History", False, f"Status: {response.status_code if response else 'No response'}")
        return False
    
    try:
        data = response.json()
        if not isinstance(data, list):
            log_test("Get Purchase History", False, "Response is not a list")
            return False
        
        # Should have at least the purchases we just made
        if len(data) < 3:
            log_test("Get Purchase History", False, f"Expected at least 3 purchases, got {len(data)}")
            return False
        
        # Check structure of first purchase
        if data:
            purchase = data[0]
            required_fields = ['id', 'user_id', 'item_id', 'item_name', 'category', 'price_brl', 'payment_method', 'transaction_id', 'status', 'created_at']
            for field in required_fields:
                if field not in purchase:
                    log_test("Get Purchase History", False, f"Missing field in purchase: {field}")
                    return False
        
        log_test("Get Purchase History", True, f"{len(data)} purchases found")
        return True
        
    except json.JSONDecodeError:
        log_test("Get Purchase History", False, "Invalid JSON response")
        return False

def test_purchase_invalid_item():
    """Test 9: POST /api/store/purchase - Try invalid item"""
    purchase_data = {
        "item_id": "nonexistent"
    }
    
    try:
        response = make_request('POST', '/store/purchase', purchase_data)
        
        if not response:
            log_test("Purchase Invalid Item", False, "No response")
            return False
        
        if response.status_code == 404:
            log_test("Purchase Invalid Item", True, "Correctly returned 404 for invalid item")
            return True
        else:
            log_test("Purchase Invalid Item", False, f"Expected 404, got {response.status_code}")
            return False
    except Exception as e:
        log_test("Purchase Invalid Item", False, f"Exception: {e}")
        return False

def test_ad_boost_1_hour_duration():
    """Test 10-12: Ad Boost - 1 Hour Duration Testing"""
    print("🎯 Testing Ad Boost - 1 Hour Duration System")
    print("   Switching to test_jobs user (has a job)...")
    
    # Switch to jobs user
    if not login_user(JOBS_USER):
        log_test("Ad Boost Setup", False, "Could not login to jobs user")
        return False
    
    # Test 10: Watch ad
    response = make_request('POST', '/ads/watch')
    
    if not response or response.status_code != 200:
        log_test("Watch Ad", False, f"Status: {response.status_code if response else 'No response'}")
        if response:
            print(f"   Response: {response.text}")
        return False
    
    try:
        data = response.json()
        
        # Check required fields
        required_fields = ['message', 'multiplier', 'ads_watched', 'expires_at', 'seconds_remaining']
        for field in required_fields:
            if field not in data:
                log_test("Watch Ad", False, f"Missing field: {field}")
                return False
        
        # Verify 1 hour duration (~3600 seconds)
        seconds_remaining = data.get('seconds_remaining', 0)
        if not (3500 <= seconds_remaining <= 3600):  # Allow some tolerance
            log_test("Watch Ad", False, f"Expected ~3600 seconds, got {seconds_remaining}")
            return False
        
        initial_multiplier = data.get('multiplier')
        log_test("Watch Ad", True, f"Ad watched! Multiplier: {initial_multiplier}x, Duration: {seconds_remaining} seconds (~1 hour)")
        
        # Test 11: Check boost status
        boost_response = make_request('GET', '/ads/current-boost')
        
        if not boost_response or boost_response.status_code != 200:
            log_test("Check Boost Status", False, f"Status: {boost_response.status_code if boost_response else 'No response'}")
            return False
        
        boost_data = boost_response.json()
        
        # Verify boost is active
        if not boost_data.get('active'):
            log_test("Check Boost Status", False, "Boost not active")
            return False
        
        # Verify multiplier
        current_multiplier = boost_data.get('multiplier')
        if current_multiplier != initial_multiplier:
            log_test("Check Boost Status", False, f"Multiplier mismatch: expected {initial_multiplier}, got {current_multiplier}")
            return False
        
        # Verify seconds remaining is still close to 1 hour
        current_seconds = boost_data.get('seconds_remaining', 0)
        if not (3400 <= current_seconds <= 3600):  # Allow more tolerance for processing time
            log_test("Check Boost Status", False, f"Unexpected seconds remaining: {current_seconds}")
            return False
        
        log_test("Check Boost Status", True, f"Boost active: {current_multiplier}x multiplier, {current_seconds} seconds remaining")
        
        # Test 12: Watch another ad to increase multiplier
        print("   Watching another ad to test multiplier increase...")
        time.sleep(1)  # Small delay
        
        second_ad_response = make_request('POST', '/ads/watch')
        
        if not second_ad_response or second_ad_response.status_code != 200:
            log_test("Watch Second Ad", False, f"Status: {second_ad_response.status_code if second_ad_response else 'No response'}")
            return False
        
        second_data = second_ad_response.json()
        new_multiplier = second_data.get('multiplier')
        new_ads_watched = second_data.get('ads_watched')
        
        # Verify multiplier increased (or stayed at max)
        if new_multiplier < initial_multiplier:
            log_test("Watch Second Ad", False, f"Multiplier decreased: {initial_multiplier} → {new_multiplier}")
            return False
        
        # Verify ads watched count increased (account for existing ads)
        if new_ads_watched <= 1:  # Should be at least 2 after watching second ad
            log_test("Watch Second Ad", False, f"Expected ads watched > 1, got {new_ads_watched}")
            return False
        
        # Verify multiplier stays constant (no decay) - check again
        final_boost_response = make_request('GET', '/ads/current-boost')
        if final_boost_response and final_boost_response.status_code == 200:
            final_boost_data = final_boost_response.json()
            final_multiplier = final_boost_data.get('multiplier')
            
            if final_multiplier != new_multiplier:
                log_test("Multiplier Consistency", False, f"Multiplier changed: {new_multiplier} → {final_multiplier}")
                return False
            
            log_test("Watch Second Ad", True, f"Multiplier increased: {initial_multiplier}x → {new_multiplier}x, Ads watched: {new_ads_watched}")
            log_test("Multiplier Consistency", True, f"Multiplier stays constant at {final_multiplier}x (no decay)")
            return True
        else:
            log_test("Multiplier Consistency", False, "Could not verify final multiplier")
            return False
        
    except json.JSONDecodeError:
        log_test("Ad Boost Testing", False, "Invalid JSON response")
        return False

def main():
    """Run all tests"""
    print("🚀 Business Empire - Game Store & Ad Boost Testing")
    print("=" * 60)
    
    # Login as main user for store testing
    if not login_user(MAIN_USER):
        print("❌ Could not login. Exiting.")
        sys.exit(1)
    
    # Game Store Tests
    print("🛒 Testing Game Store System")
    print("-" * 30)
    
    tests = [
        ("Get Store Items", test_get_store_items),
        ("Get Store Items Filtered", test_get_store_items_filtered),
        ("Purchase Money Pack", test_purchase_money_pack),
        ("Purchase XP Boost", test_purchase_xp_boost),
        ("Purchase Earnings Boost", test_purchase_earnings_boost),
        ("Get Purchase History", test_get_purchase_history),
        ("Purchase Invalid Item", test_purchase_invalid_item),
    ]
    
    store_results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            store_results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} - Exception: {e}")
            store_results.append((test_name, False))
    
    # Ad Boost Tests
    print("\n📺 Testing Ad Boost - 1 Hour Duration System")
    print("-" * 40)
    
    try:
        ad_boost_result = test_ad_boost_1_hour_duration()
    except Exception as e:
        print(f"❌ Ad Boost Testing - Exception: {e}")
        ad_boost_result = False
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    print("\n🛒 Game Store System:")
    store_passed = 0
    for test_name, result in store_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} {test_name}")
        if result:
            store_passed += 1
    
    print(f"\n📺 Ad Boost System:")
    status = "✅ PASS" if ad_boost_result else "❌ FAIL"
    print(f"   {status} Ad Boost - 1 Hour Duration")
    
    total_tests = len(store_results) + 1
    total_passed = store_passed + (1 if ad_boost_result else 0)
    
    print(f"\n🎯 OVERALL RESULTS:")
    print(f"   Total Tests: {total_tests}")
    print(f"   Passed: {total_passed}")
    print(f"   Failed: {total_tests - total_passed}")
    print(f"   Success Rate: {(total_passed/total_tests)*100:.1f}%")
    
    if total_passed == total_tests:
        print("\n🎉 ALL TESTS PASSED! Game Store and Ad Boost systems are working correctly.")
        return True
    else:
        print(f"\n⚠️  {total_tests - total_passed} test(s) failed. Please check the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)