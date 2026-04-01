#!/usr/bin/env python3
"""
Business Empire Rankings System Test
Focus: Testing Rankings API endpoints
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BASE_URL = "https://career-mogul-1.preview.emergentagent.com/api"
TEST_USER = {
    "email": "teste@businessempire.com",
    "password": "teste123",
    "name": "Jogador Teste"
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
            headers['Content-Type'] = 'application/json'
            response = requests.post(url, json=data, headers=headers, timeout=30)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        return response
    except requests.exceptions.Timeout:
        print(f"Request timeout for {method} {url}")
        return None
    except requests.exceptions.ConnectionError as e:
        print(f"Connection error for {method} {url}: {e}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Request failed for {method} {url}: {e}")
        return None

def test_user_login():
    """Test: POST /api/auth/login"""
    global auth_token, user_data
    
    login_data = {
        "email": TEST_USER["email"],
        "password": TEST_USER["password"]
    }
    
    response = make_request('POST', '/auth/login', login_data)
    
    if not response or response.status_code != 200:
        log_test("User Login", False, f"Status: {response.status_code if response else 'No response'}")
        return False
    
    try:
        data = response.json()
        auth_token = data['token']
        user_data = data['user']
        log_test("User Login", True, f"User logged in: {user_data['email']}")
        return True
    except json.JSONDecodeError:
        log_test("User Login", False, "Invalid JSON response")
        return False

def test_get_weekly_rankings():
    """Test: GET /api/rankings?period=weekly"""
    response = make_request('GET', '/rankings?period=weekly')
    
    if not response:
        log_test("Get Weekly Rankings", False, "Request failed")
        return False
    
    if response.status_code != 200:
        log_test("Get Weekly Rankings", False, f"Status: {response.status_code}, Response: {response.text}")
        return False
    
    try:
        data = response.json()
        
        # Check required top-level fields
        required_fields = ['period', 'updated_at', 'total_players', 'rankings', 'current_user']
        for field in required_fields:
            if field not in data:
                log_test("Get Weekly Rankings", False, f"Missing field: {field}")
                return False
        
        # Verify period is correct
        if data['period'] != 'weekly':
            log_test("Get Weekly Rankings", False, f"Expected period 'weekly', got '{data['period']}'")
            return False
        
        # Check rankings array
        rankings = data['rankings']
        if not isinstance(rankings, list):
            log_test("Get Weekly Rankings", False, "Rankings is not a list")
            return False
        
        # Check each ranking entry structure
        for i, ranking in enumerate(rankings):
            required_ranking_fields = [
                'position', 'user_id', 'name', 'avatar_color', 'avatar_icon', 
                'level', 'total_net_worth', 'cash', 'investment_value', 
                'companies_value', 'assets_value', 'num_companies', 
                'num_assets', 'num_investments', 'position_change'
            ]
            for field in required_ranking_fields:
                if field not in ranking:
                    log_test("Get Weekly Rankings", False, f"Missing field '{field}' in ranking entry {i}")
                    return False
        
        # Verify rankings are sorted by total_net_worth descending
        for i in range(len(rankings) - 1):
            if rankings[i]['total_net_worth'] < rankings[i + 1]['total_net_worth']:
                log_test("Get Weekly Rankings", False, f"Rankings not sorted correctly: position {i+1} has lower net worth than position {i+2}")
                return False
        
        # Check current_user structure
        current_user = data['current_user']
        if current_user is not None:
            # Verify current_user has the correct user_id matching the logged-in user
            if 'user_id' not in current_user:
                log_test("Get Weekly Rankings", False, "Missing user_id in current_user")
                return False
            
            if current_user['user_id'] != user_data['id']:
                log_test("Get Weekly Rankings", False, f"Current user ID mismatch: expected {user_data['id']}, got {current_user['user_id']}")
                return False
            
            # Check current_user has all required fields
            for field in required_ranking_fields:
                if field not in current_user:
                    log_test("Get Weekly Rankings", False, f"Missing field '{field}' in current_user")
                    return False
        
        log_test("Get Weekly Rankings", True, f"Retrieved weekly rankings: {data['total_players']} players, top player net worth: R$ {rankings[0]['total_net_worth']:,.2f}")
        return True
        
    except json.JSONDecodeError:
        log_test("Get Weekly Rankings", False, "Invalid JSON response")
        return False

def test_get_monthly_rankings():
    """Test: GET /api/rankings?period=monthly"""
    response = make_request('GET', '/rankings?period=monthly')
    
    if not response:
        log_test("Get Monthly Rankings", False, "Request failed")
        return False
    
    if response.status_code != 200:
        log_test("Get Monthly Rankings", False, f"Status: {response.status_code}, Response: {response.text}")
        return False
    
    try:
        data = response.json()
        
        # Check required top-level fields
        required_fields = ['period', 'updated_at', 'total_players', 'rankings', 'current_user']
        for field in required_fields:
            if field not in data:
                log_test("Get Monthly Rankings", False, f"Missing field: {field}")
                return False
        
        # Verify period is correct
        if data['period'] != 'monthly':
            log_test("Get Monthly Rankings", False, f"Expected period 'monthly', got '{data['period']}'")
            return False
        
        # Check rankings array
        rankings = data['rankings']
        if not isinstance(rankings, list):
            log_test("Get Monthly Rankings", False, "Rankings is not a list")
            return False
        
        # Check each ranking entry structure
        for i, ranking in enumerate(rankings):
            required_ranking_fields = [
                'position', 'user_id', 'name', 'avatar_color', 'avatar_icon', 
                'level', 'total_net_worth', 'cash', 'investment_value', 
                'companies_value', 'assets_value', 'num_companies', 
                'num_assets', 'num_investments', 'position_change'
            ]
            for field in required_ranking_fields:
                if field not in ranking:
                    log_test("Get Monthly Rankings", False, f"Missing field '{field}' in ranking entry {i}")
                    return False
        
        # Verify rankings are sorted by total_net_worth descending
        for i in range(len(rankings) - 1):
            if rankings[i]['total_net_worth'] < rankings[i + 1]['total_net_worth']:
                log_test("Get Monthly Rankings", False, f"Rankings not sorted correctly: position {i+1} has lower net worth than position {i+2}")
                return False
        
        # Check current_user structure
        current_user = data['current_user']
        if current_user is not None:
            # Verify current_user has the correct user_id matching the logged-in user
            if 'user_id' not in current_user:
                log_test("Get Monthly Rankings", False, "Missing user_id in current_user")
                return False
            
            if current_user['user_id'] != user_data['id']:
                log_test("Get Monthly Rankings", False, f"Current user ID mismatch: expected {user_data['id']}, got {current_user['user_id']}")
                return False
            
            # Check current_user has all required fields
            for field in required_ranking_fields:
                if field not in current_user:
                    log_test("Get Monthly Rankings", False, f"Missing field '{field}' in current_user")
                    return False
        
        log_test("Get Monthly Rankings", True, f"Retrieved monthly rankings: {data['total_players']} players, top player net worth: R$ {rankings[0]['total_net_worth']:,.2f}")
        return True
        
    except json.JSONDecodeError:
        log_test("Get Monthly Rankings", False, "Invalid JSON response")
        return False

def test_rankings_authentication():
    """Test: Verify rankings endpoints require authentication"""
    global auth_token
    # Test without auth token
    old_token = auth_token
    auth_token = None
    
    # Make request without authentication
    url = f"{BASE_URL}/rankings?period=weekly"
    try:
        response = requests.get(url, timeout=30)
        auth_token = old_token  # Restore token
        
        if response.status_code not in [401, 403]:
            log_test("Rankings Authentication", False, f"Expected 401/403, got {response.status_code}")
            return False
        
        log_test("Rankings Authentication", True, "Properly rejected unauthorized request to rankings")
        return True
        
    except Exception as e:
        auth_token = old_token  # Restore token
        log_test("Rankings Authentication", False, f"Request failed: {str(e)}")
        return False

def main():
    """Run all rankings tests"""
    print("=" * 60)
    print("BUSINESS EMPIRE RANKINGS SYSTEM TEST")
    print("Focus: Testing Rankings API endpoints")
    print("=" * 60)
    print()
    
    tests = [
        ("User Login", test_user_login),
        ("Get Weekly Rankings", test_get_weekly_rankings),
        ("Get Monthly Rankings", test_get_monthly_rankings),
        ("Rankings Authentication", test_rankings_authentication),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            log_test(test_name, False, f"Exception: {str(e)}")
            failed += 1
    
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"✅ PASSED: {passed}")
    print(f"❌ FAILED: {failed}")
    print(f"📊 TOTAL:  {passed + failed}")
    print()
    
    if failed == 0:
        print("🎉 ALL RANKINGS TESTS PASSED! Rankings system working correctly.")
        print("✅ Weekly and monthly rankings endpoints verified")
        print("✅ Response structure validation complete")
        print("✅ Sorting by net worth verified")
        print("✅ Authentication requirement verified")
        print("✅ Current user identification working")
    else:
        print("⚠️  Some tests failed. Check the details above.")
        if failed > passed:
            print("❌ Major issues detected. Rankings system may not be working properly.")
    
    print("=" * 60)
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)