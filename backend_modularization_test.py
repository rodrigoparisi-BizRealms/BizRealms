#!/usr/bin/env python3
"""
Backend API Testing for BizRealms - Post-Modularization Comprehensive Testing
Testing all 11 route modules after backend refactoring from monolithic server.py
"""

import requests
import json
import sys

# Configuration
BASE_URL = "https://career-mogul-1.preview.emergentagent.com"
API_BASE = f"{BASE_URL}/api"
TEST_EMAIL = "teste@businessempire.com"
TEST_PASSWORD = "teste123"

def test_auth_module():
    """Test Auth module - POST /api/auth/login"""
    print("🔐 Testing Auth Module - Login...")
    
    login_data = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    }
    
    try:
        response = requests.post(f"{API_BASE}/auth/login", json=login_data)
        print(f"Auth Login Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("token") or data.get("access_token")
            if token:
                print("✅ Auth module working - JWT token received")
                return token
            else:
                print("❌ Auth module failed - No token in response")
                print(f"Response: {data}")
                return None
        else:
            print(f"❌ Auth module failed - Status: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Auth module error: {str(e)}")
        return None

def test_user_module(token):
    """Test User module - GET /api/user/me"""
    print("\n👤 Testing User Module - Get Profile...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{API_BASE}/user/me", headers=headers)
        print(f"User Profile Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ User module working - Profile retrieved")
            print(f"User: {data.get('name', 'N/A')} ({data.get('email', 'N/A')})")
            print(f"Level: {data.get('level', 'N/A')}, Money: R$ {data.get('money', 'N/A')}")
            return True
        else:
            print(f"❌ User module failed - Status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ User module error: {str(e)}")
        return False

def test_user_stats_module(token):
    """Test User Stats - GET /api/user/stats"""
    print("\n📊 Testing User Stats Module...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{API_BASE}/user/stats", headers=headers)
        print(f"User Stats Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ User stats module working")
            print(f"Level: {data.get('level', 'N/A')}, XP: {data.get('experience_points', 'N/A')}")
            print(f"Education: {data.get('education_count', 'N/A')}, Certifications: {data.get('certification_count', 'N/A')}")
            return True
        else:
            print(f"❌ User stats module failed - Status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ User stats module error: {str(e)}")
        return False

def test_jobs_module(token):
    """Test Jobs module - GET /api/jobs/available-for-level"""
    print("\n💼 Testing Jobs Module - Available Jobs...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{API_BASE}/jobs/available-for-level", headers=headers)
        print(f"Jobs Available Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Jobs module working")
            print(f"Available jobs: {len(data)} jobs found")
            if data:
                print(f"Sample job: {data[0].get('title', 'N/A')} - R$ {data[0].get('salary', 'N/A')}")
            return True
        else:
            print(f"❌ Jobs module failed - Status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Jobs module error: {str(e)}")
        return False

def test_investments_module():
    """Test Investments module - GET /api/investments/market (no auth needed)"""
    print("\n📈 Testing Investments Module - Market Data...")
    
    try:
        response = requests.get(f"{API_BASE}/investments/market")
        print(f"Investment Market Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Investments module working")
            print(f"Market assets: {len(data)} assets available")
            if data:
                print(f"Sample asset: {data[0].get('name', 'N/A')} - R$ {data[0].get('price', 'N/A')}")
            return True
        else:
            print(f"❌ Investments module failed - Status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Investments module error: {str(e)}")
        return False

def test_companies_module(token):
    """Test Companies module - GET /api/companies/owned"""
    print("\n🏢 Testing Companies Module - Owned Companies...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{API_BASE}/companies/owned", headers=headers)
        print(f"Companies Owned Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Companies module working")
            print(f"Owned companies: {len(data)} companies")
            if data:
                print(f"Sample company: {data[0].get('name', 'N/A')} - Revenue: R$ {data[0].get('monthly_revenue', 'N/A')}")
            return True
        else:
            print(f"❌ Companies module failed - Status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Companies module error: {str(e)}")
        return False

def test_assets_module(token):
    """Test Assets module - GET /api/assets/owned"""
    print("\n🏠 Testing Assets Module - Owned Assets...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{API_BASE}/assets/owned", headers=headers)
        print(f"Assets Owned Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Assets module working")
            print(f"Owned assets: {len(data)} assets")
            if data:
                print(f"Sample asset: {data[0].get('name', 'N/A')} - Value: R$ {data[0].get('current_value', 'N/A')}")
            return True
        else:
            print(f"❌ Assets module failed - Status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Assets module error: {str(e)}")
        return False

def test_rankings_module(token):
    """Test Rankings module - GET /api/rankings?period=weekly"""
    print("\n🏆 Testing Rankings Module - Weekly Rankings...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{API_BASE}/rankings?period=weekly", headers=headers)
        print(f"Rankings Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Rankings module working")
            print(f"Total players: {data.get('total_players', 'N/A')}")
            rankings = data.get('rankings', [])
            if rankings:
                print(f"Top player: {rankings[0].get('name', 'N/A')} - Net Worth: R$ {rankings[0].get('total_net_worth', 'N/A')}")
            return True
        else:
            print(f"❌ Rankings module failed - Status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Rankings module error: {str(e)}")
        return False

def test_store_module(token):
    """Test Store module - GET /api/store/items"""
    print("\n🛒 Testing Store Module - Store Items...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{API_BASE}/store/items", headers=headers)
        print(f"Store Items Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Store module working")
            print(f"Store items: {len(data)} items available")
            if data:
                print(f"Sample item: {data[0].get('name', 'N/A')} - Price: R$ {data[0].get('price_brl', 'N/A')}")
            return True
        else:
            print(f"❌ Store module failed - Status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Store module error: {str(e)}")
        return False

def test_bank_module(token):
    """Test Bank module - GET /api/bank/account"""
    print("\n🏦 Testing Bank Module - Bank Account...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{API_BASE}/bank/account", headers=headers)
        print(f"Bank Account Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Bank module working")
            print(f"Account balance: R$ {data.get('balance', 'N/A')}")
            credit_card = data.get('credit_card', {})
            if credit_card:
                print(f"Credit card limit: R$ {credit_card.get('limit', 'N/A')}")
            return True
        else:
            print(f"❌ Bank module failed - Status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Bank module error: {str(e)}")
        return False

def test_notifications_module(token):
    """Test Notifications module - GET /api/notifications"""
    print("\n🔔 Testing Notifications Module...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{API_BASE}/notifications", headers=headers)
        print(f"Notifications Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Notifications module working")
            notifications = data.get('notifications', [])
            print(f"Notifications: {len(notifications)} notifications")
            print(f"Unread count: {data.get('unread_count', 'N/A')}")
            return True
        else:
            print(f"❌ Notifications module failed - Status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Notifications module error: {str(e)}")
        return False

def test_paypal_module(token):
    """Test PayPal module - POST /api/rewards/update-paypal"""
    print("\n💳 Testing PayPal Module - Update PayPal Email...")
    
    headers = {"Authorization": f"Bearer {token}"}
    paypal_data = {
        "paypal_email": "test@paypal.com"
    }
    
    try:
        response = requests.post(f"{API_BASE}/rewards/update-paypal", json=paypal_data, headers=headers)
        print(f"PayPal Update Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ PayPal module working")
            print(f"Response: {data.get('message', 'PayPal email updated')}")
            return True
        else:
            print(f"❌ PayPal module failed - Status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ PayPal module error: {str(e)}")
        return False

def test_legal_pages():
    """Test Legal pages - GET /legal/terms (no auth, should return HTML)"""
    print("\n📄 Testing Legal Pages - Terms of Service...")
    
    try:
        response = requests.get(f"{BASE_URL}/legal/terms")
        print(f"Legal Terms Status: {response.status_code}")
        
        if response.status_code == 200:
            content = response.text
            print("✅ Legal pages working")
            print(f"Content type: {response.headers.get('content-type', 'N/A')}")
            print(f"Content length: {len(content)} characters")
            if "terms" in content.lower() or "termos" in content.lower():
                print("✅ Terms content detected")
            return True
        else:
            print(f"❌ Legal pages failed - Status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Legal pages error: {str(e)}")
        return False

def main():
    """Run all modularization tests"""
    print("🚀 Starting BizRealms Post-Modularization Comprehensive Tests")
    print(f"Backend URL: {BASE_URL}")
    print(f"API Base: {API_BASE}")
    print(f"Test User: {TEST_EMAIL}")
    print("=" * 80)
    
    tests_passed = 0
    total_tests = 13
    
    # 1. Auth module
    token = test_auth_module()
    if token:
        tests_passed += 1
    else:
        print("\n❌ Cannot continue without valid token")
        sys.exit(1)
    
    # 2. User module
    if test_user_module(token):
        tests_passed += 1
    
    # 3. User stats
    if test_user_stats_module(token):
        tests_passed += 1
    
    # 4. Jobs module
    if test_jobs_module(token):
        tests_passed += 1
    
    # 5. Investments module (no auth needed)
    if test_investments_module():
        tests_passed += 1
    
    # 6. Companies module
    if test_companies_module(token):
        tests_passed += 1
    
    # 7. Assets module
    if test_assets_module(token):
        tests_passed += 1
    
    # 8. Rankings module
    if test_rankings_module(token):
        tests_passed += 1
    
    # 9. Store module
    if test_store_module(token):
        tests_passed += 1
    
    # 10. Bank module
    if test_bank_module(token):
        tests_passed += 1
    
    # 11. Notifications module
    if test_notifications_module(token):
        tests_passed += 1
    
    # 12. PayPal module
    if test_paypal_module(token):
        tests_passed += 1
    
    # 13. Legal pages
    if test_legal_pages():
        tests_passed += 1
    
    # Summary
    print("\n" + "=" * 80)
    print(f"🎯 MODULARIZATION TEST SUMMARY: {tests_passed}/{total_tests} modules working")
    
    if tests_passed == total_tests:
        print("🎉 ALL MODULES WORKING - Backend modularization successful!")
        return True
    else:
        failed_tests = total_tests - tests_passed
        print(f"❌ {failed_tests} modules failed - Modularization issues detected")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)