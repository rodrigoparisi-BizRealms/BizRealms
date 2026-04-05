#!/usr/bin/env python3
"""
Backend API Testing for BizRealms - Personal Data and PayPal Account Flow
Testing the specific flow requested in the review.
"""

import requests
import json
import sys

# Configuration
BASE_URL = "https://career-mogul-1.preview.emergentagent.com/api"
TEST_EMAIL = "teste@businessempire.com"
TEST_PASSWORD = "teste123"

def test_login():
    """Test user login and get JWT token"""
    print("🔐 Testing Login...")
    
    login_data = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        print(f"Login Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("token") or data.get("access_token")
            if token:
                print("✅ Login successful - JWT token received")
                return token
            else:
                print("❌ Login failed - No token in response")
                print(f"Response: {data}")
                return None
        else:
            print(f"❌ Login failed - Status: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Login error: {str(e)}")
        return None

def test_save_personal_data(token):
    """Test saving personal data with new fields"""
    print("\n👤 Testing Save Personal Data with new fields...")
    
    headers = {"Authorization": f"Bearer {token}"}
    personal_data = {
        "full_name": "João da Silva",
        "identity_document": "123.456.789-00",
        "country": "Brasil",
        "phone": "+5511999999999",
        "address": "Rua Teste 123",
        "city": "São Paulo",
        "state": "SP",
        "zip_code": "01234-567"
    }
    
    try:
        response = requests.put(f"{BASE_URL}/user/personal-data", json=personal_data, headers=headers)
        print(f"Personal Data Update Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Personal data saved successfully")
            print(f"Response: {data}")
            return True
        else:
            print(f"❌ Personal data save failed - Status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Personal data save error: {str(e)}")
        return False

def test_verify_personal_data(token):
    """Test verifying personal data was saved correctly"""
    print("\n🔍 Testing Verify Personal Data Saved...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{BASE_URL}/user/me", headers=headers)
        print(f"Get User Profile Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Check for required fields
            required_fields = ["identity_document", "country", "full_name"]
            missing_fields = []
            
            for field in required_fields:
                if field not in data or data[field] is None:
                    missing_fields.append(field)
            
            if not missing_fields:
                print("✅ Personal data verification successful")
                print(f"Full Name: {data.get('full_name')}")
                print(f"Identity Document: {data.get('identity_document')}")
                print(f"Country: {data.get('country')}")
                print(f"Phone: {data.get('phone')}")
                print(f"Address: {data.get('address')}")
                print(f"City: {data.get('city')}")
                print(f"State: {data.get('state')}")
                print(f"Zip Code: {data.get('zip_code')}")
                return True
            else:
                print(f"❌ Personal data verification failed - Missing fields: {missing_fields}")
                print(f"Available fields: {list(data.keys())}")
                return False
        else:
            print(f"❌ Get user profile failed - Status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Personal data verification error: {str(e)}")
        return False

def test_save_paypal_account(token):
    """Test saving PayPal account"""
    print("\n💳 Testing Save PayPal Account...")
    
    headers = {"Authorization": f"Bearer {token}"}
    paypal_data = {
        "paypal_email": "joao@paypal.com"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/rewards/update-paypal", json=paypal_data, headers=headers)
        print(f"PayPal Update Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ PayPal account saved successfully")
            print(f"Response: {data}")
            return True
        else:
            print(f"❌ PayPal account save failed - Status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ PayPal account save error: {str(e)}")
        return False

def test_verify_paypal_and_personal_data(token):
    """Test verifying both PayPal and personal data are present"""
    print("\n🔍 Testing Verify PayPal + Personal Data Together...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{BASE_URL}/user/me", headers=headers)
        print(f"Get User Profile Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Check for both PayPal and personal data fields
            paypal_email = data.get('paypal_email')
            identity_document = data.get('identity_document')
            
            if paypal_email and identity_document:
                print("✅ Both PayPal and personal data verification successful")
                print(f"PayPal Email: {paypal_email}")
                print(f"Identity Document: {identity_document}")
                print(f"Full Name: {data.get('full_name')}")
                print(f"Country: {data.get('country')}")
                return True
            else:
                print(f"❌ Verification failed - PayPal: {paypal_email}, Identity: {identity_document}")
                print(f"Available fields: {list(data.keys())}")
                return False
        else:
            print(f"❌ Get user profile failed - Status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Combined verification error: {str(e)}")
        return False

def test_delete_paypal(token):
    """Test deleting PayPal account"""
    print("\n🗑️ Testing Delete PayPal Account...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.delete(f"{BASE_URL}/rewards/delete-paypal", headers=headers)
        print(f"PayPal Delete Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ PayPal account deleted successfully")
            print(f"Response: {data}")
            return True
        else:
            print(f"❌ PayPal account delete failed - Status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ PayPal account delete error: {str(e)}")
        return False

def test_verify_paypal_deletion(token):
    """Test verifying PayPal account was deleted"""
    print("\n🔍 Testing Verify PayPal Deletion...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{BASE_URL}/user/me", headers=headers)
        print(f"Get User Profile Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            paypal_email = data.get('paypal_email')
            identity_document = data.get('identity_document')
            
            if paypal_email is None and identity_document is not None:
                print("✅ PayPal deletion verification successful")
                print(f"PayPal Email: {paypal_email} (correctly deleted)")
                print(f"Identity Document: {identity_document} (still present)")
                return True
            else:
                print(f"❌ PayPal deletion verification failed")
                print(f"PayPal Email: {paypal_email} (should be None)")
                print(f"Identity Document: {identity_document} (should still exist)")
                return False
        else:
            print(f"❌ Get user profile failed - Status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ PayPal deletion verification error: {str(e)}")
        return False

def main():
    """Run all tests in sequence"""
    print("🚀 Starting BizRealms Personal Data and PayPal Account Flow Tests")
    print(f"Backend URL: {BASE_URL}")
    print(f"Test User: {TEST_EMAIL}")
    print("=" * 70)
    
    # Test sequence
    tests_passed = 0
    total_tests = 7
    
    # 1. Login
    token = test_login()
    if token:
        tests_passed += 1
    else:
        print("\n❌ Cannot continue without valid token")
        sys.exit(1)
    
    # 2. Save Personal Data
    if test_save_personal_data(token):
        tests_passed += 1
    
    # 3. Verify Personal Data
    if test_verify_personal_data(token):
        tests_passed += 1
    
    # 4. Save PayPal Account
    if test_save_paypal_account(token):
        tests_passed += 1
    
    # 5. Verify PayPal + Personal Data
    if test_verify_paypal_and_personal_data(token):
        tests_passed += 1
    
    # 6. Delete PayPal
    if test_delete_paypal(token):
        tests_passed += 1
    
    # 7. Verify PayPal Deletion
    if test_verify_paypal_deletion(token):
        tests_passed += 1
    
    # Summary
    print("\n" + "=" * 70)
    print(f"🎯 TEST SUMMARY: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 ALL TESTS PASSED - Personal Data and PayPal flow working correctly!")
        return True
    else:
        print(f"❌ {total_tests - tests_passed} tests failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)