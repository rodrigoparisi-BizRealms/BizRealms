#!/usr/bin/env python3
"""
Backend API Testing for BizRealms - Post-Modularization Final Verification
Testing all 13 route modules after backend refactoring from monolithic server.py
"""

import requests
import json
import sys

# Configuration
BASE_URL = "https://career-mogul-1.preview.emergentagent.com"
API_BASE = f"{BASE_URL}/api"
TEST_EMAIL = "teste@businessempire.com"
TEST_PASSWORD = "teste123"

def test_all_modules():
    """Test all modules in sequence and return results"""
    print("🚀 BizRealms Post-Modularization Final Verification")
    print(f"Backend URL: {BASE_URL}")
    print("=" * 60)
    
    results = {}
    
    # 1. Auth module
    print("🔐 Testing Auth Module...")
    login_data = {"email": TEST_EMAIL, "password": TEST_PASSWORD}
    try:
        response = requests.post(f"{API_BASE}/auth/login", json=login_data)
        if response.status_code == 200:
            token = response.json().get("token") or response.json().get("access_token")
            if token:
                results["Auth"] = "✅ WORKING"
                headers = {"Authorization": f"Bearer {token}"}
            else:
                results["Auth"] = "❌ FAILED - No token"
                return results
        else:
            results["Auth"] = f"❌ FAILED - Status {response.status_code}"
            return results
    except Exception as e:
        results["Auth"] = f"❌ ERROR - {str(e)}"
        return results
    
    # Test all other modules
    tests = [
        ("User", "GET", "/user/me", True),
        ("User Stats", "GET", "/user/stats", True),
        ("Jobs", "GET", "/jobs/available-for-level", True),
        ("Investments", "GET", "/investments/market", False),  # No auth needed
        ("Companies", "GET", "/companies/owned", True),
        ("Assets", "GET", "/assets/owned", True),
        ("Rankings", "GET", "/rankings?period=weekly", True),
        ("Store", "GET", "/store/items", True),
        ("Bank", "GET", "/bank/account", True),
        ("Notifications", "GET", "/notifications", True),
        ("PayPal", "POST", "/rewards/update-paypal", True, {"paypal_email": "test@paypal.com"}),
        ("Legal", "GET", "/legal/terms", False, None, BASE_URL)  # Different base URL
    ]
    
    for test_info in tests:
        module_name = test_info[0]
        method = test_info[1]
        endpoint = test_info[2]
        needs_auth = test_info[3]
        data = test_info[4] if len(test_info) > 4 else None
        base_url = test_info[5] if len(test_info) > 5 else API_BASE
        
        print(f"🔍 Testing {module_name} Module...")
        
        try:
            url = f"{base_url}{endpoint}"
            request_headers = headers if needs_auth else {}
            
            if method == "GET":
                response = requests.get(url, headers=request_headers)
            elif method == "POST":
                response = requests.post(url, json=data, headers=request_headers)
            
            if response.status_code == 200:
                results[module_name] = "✅ WORKING"
            else:
                results[module_name] = f"❌ FAILED - Status {response.status_code}"
                
        except Exception as e:
            results[module_name] = f"❌ ERROR - {str(e)}"
    
    return results

def main():
    """Run all tests and display results"""
    results = test_all_modules()
    
    print("\n" + "=" * 60)
    print("🎯 FINAL MODULARIZATION TEST RESULTS:")
    print("=" * 60)
    
    working_count = 0
    total_count = len(results)
    
    for module, status in results.items():
        print(f"{module:15} | {status}")
        if "✅ WORKING" in status:
            working_count += 1
    
    print("=" * 60)
    print(f"📊 SUMMARY: {working_count}/{total_count} modules working")
    
    if working_count == total_count:
        print("🎉 ALL MODULES WORKING - Backend modularization successful!")
        return True
    else:
        failed_count = total_count - working_count
        print(f"⚠️  {failed_count} modules have issues")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)