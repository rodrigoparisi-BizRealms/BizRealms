#!/usr/bin/env python3
"""
PayPal Rewards System Testing Script
Tests the migration from PIX to PayPal for BizRealms game app
"""

import requests
import json
import sys
from typing import Dict, Any

# Backend URL from frontend/.env
BACKEND_URL = "https://career-mogul-1.preview.emergentagent.com/api"

# Test credentials from test_credentials.md
TEST_EMAIL = "teste@businessempire.com"
TEST_PASSWORD = "teste123"

class PayPalRewardsTest:
    def __init__(self):
        self.token = None
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def log(self, message: str, level: str = "INFO"):
        """Log test messages"""
        print(f"[{level}] {message}")
    
    def login(self) -> bool:
        """Test 1: Login with credentials to get JWT token"""
        self.log("=== TEST 1: User Login ===")
        
        login_data = {
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        }
        
        try:
            response = self.session.post(f"{BACKEND_URL}/auth/login", json=login_data)
            self.log(f"Login response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get('token')  # Backend returns 'token' not 'access_token'
                if self.token:
                    self.session.headers.update({'Authorization': f'Bearer {self.token}'})
                    self.log("✅ Login successful, JWT token obtained")
                    return True
                else:
                    self.log("❌ Login failed: No access token in response", "ERROR")
                    return False
            else:
                self.log(f"❌ Login failed with status {response.status_code}: {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Login failed with exception: {str(e)}", "ERROR")
            return False
    
    def update_paypal_account(self) -> bool:
        """Test 2: Update PayPal Account"""
        self.log("=== TEST 2: Update PayPal Account ===")
        
        paypal_data = {
            "paypal_email": "test@paypal.com"
        }
        
        try:
            response = self.session.post(f"{BACKEND_URL}/rewards/update-paypal", json=paypal_data)
            self.log(f"Update PayPal response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"Response: {json.dumps(data, indent=2)}")
                if data.get('success'):
                    self.log("✅ PayPal account updated successfully")
                    return True
                else:
                    self.log("❌ PayPal update failed: success=false", "ERROR")
                    return False
            else:
                self.log(f"❌ PayPal update failed with status {response.status_code}: {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ PayPal update failed with exception: {str(e)}", "ERROR")
            return False
    
    def verify_paypal_saved(self) -> bool:
        """Test 3: Verify PayPal was saved in user profile"""
        self.log("=== TEST 3: Verify PayPal Email Saved ===")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/user/me")
            self.log(f"Get user profile response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                paypal_email = data.get('paypal_email')
                self.log(f"PayPal email in profile: {paypal_email}")
                
                if paypal_email == "test@paypal.com":
                    self.log("✅ PayPal email correctly saved in user profile")
                    return True
                else:
                    self.log(f"❌ PayPal email not saved correctly. Expected: test@paypal.com, Got: {paypal_email}", "ERROR")
                    return False
            else:
                self.log(f"❌ Get user profile failed with status {response.status_code}: {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Get user profile failed with exception: {str(e)}", "ERROR")
            return False
    
    def delete_paypal_account(self) -> bool:
        """Test 4: Delete PayPal Account"""
        self.log("=== TEST 4: Delete PayPal Account ===")
        
        try:
            response = self.session.delete(f"{BACKEND_URL}/rewards/delete-paypal")
            self.log(f"Delete PayPal response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"Response: {json.dumps(data, indent=2)}")
                if data.get('success'):
                    self.log("✅ PayPal account deleted successfully")
                    return True
                else:
                    self.log("❌ PayPal deletion failed: success=false", "ERROR")
                    return False
            else:
                self.log(f"❌ PayPal deletion failed with status {response.status_code}: {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ PayPal deletion failed with exception: {str(e)}", "ERROR")
            return False
    
    def verify_paypal_deleted(self) -> bool:
        """Test 5: Verify PayPal deletion"""
        self.log("=== TEST 5: Verify PayPal Email Deleted ===")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/user/me")
            self.log(f"Get user profile response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                paypal_email = data.get('paypal_email')
                self.log(f"PayPal email in profile after deletion: {paypal_email}")
                
                if not paypal_email or paypal_email == "":
                    self.log("✅ PayPal email correctly removed from user profile")
                    return True
                else:
                    self.log(f"❌ PayPal email not deleted correctly. Expected: empty/null, Got: {paypal_email}", "ERROR")
                    return False
            else:
                self.log(f"❌ Get user profile failed with status {response.status_code}: {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Get user profile failed with exception: {str(e)}", "ERROR")
            return False
    
    def test_prize_pool_endpoint(self) -> bool:
        """Test 6: Prize Pool endpoint should return has_paypal field (not has_pix_key)"""
        self.log("=== TEST 6: Prize Pool Endpoint (has_paypal field) ===")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/rewards/prize-pool")
            self.log(f"Prize pool response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"Prize pool response keys: {list(data.keys())}")
                
                # Check for has_paypal field
                has_paypal = data.get('has_paypal')
                has_pix_key = data.get('has_pix_key')
                
                self.log(f"has_paypal field: {has_paypal}")
                self.log(f"has_pix_key field: {has_pix_key}")
                
                if 'has_paypal' in data and 'has_pix_key' not in data:
                    self.log("✅ Prize pool endpoint correctly returns has_paypal field (no has_pix_key)")
                    return True
                elif 'has_pix_key' in data:
                    self.log("❌ Prize pool endpoint still contains has_pix_key field (should be removed)", "ERROR")
                    return False
                else:
                    self.log("❌ Prize pool endpoint missing has_paypal field", "ERROR")
                    return False
            else:
                self.log(f"❌ Prize pool endpoint failed with status {response.status_code}: {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Prize pool endpoint failed with exception: {str(e)}", "ERROR")
            return False
    
    def test_old_pix_endpoints_removed(self) -> bool:
        """Test 7 & 8: Verify old PIX endpoints are gone"""
        self.log("=== TEST 7 & 8: Verify Old PIX Endpoints Removed ===")
        
        success = True
        
        # Test update-pix endpoint
        try:
            response = self.session.post(f"{BACKEND_URL}/rewards/update-pix", json={"pix_key": "test"})
            self.log(f"Update PIX endpoint response status: {response.status_code}")
            
            if response.status_code in [404, 405]:
                self.log("✅ POST /api/rewards/update-pix correctly returns 404/405 (endpoint removed)")
            else:
                self.log(f"❌ POST /api/rewards/update-pix should return 404/405, got {response.status_code}", "ERROR")
                success = False
                
        except Exception as e:
            self.log(f"Update PIX endpoint test failed with exception: {str(e)}", "ERROR")
            success = False
        
        # Test delete-pix endpoint
        try:
            response = self.session.delete(f"{BACKEND_URL}/rewards/delete-pix")
            self.log(f"Delete PIX endpoint response status: {response.status_code}")
            
            if response.status_code in [404, 405]:
                self.log("✅ DELETE /api/rewards/delete-pix correctly returns 404/405 (endpoint removed)")
            else:
                self.log(f"❌ DELETE /api/rewards/delete-pix should return 404/405, got {response.status_code}", "ERROR")
                success = False
                
        except Exception as e:
            self.log(f"Delete PIX endpoint test failed with exception: {str(e)}", "ERROR")
            success = False
        
        return success
    
    def run_all_tests(self) -> Dict[str, bool]:
        """Run all PayPal migration tests"""
        self.log("🚀 Starting PayPal Rewards System Tests")
        self.log(f"Backend URL: {BACKEND_URL}")
        self.log(f"Test User: {TEST_EMAIL}")
        
        results = {}
        
        # Test 1: Login
        results['login'] = self.login()
        if not results['login']:
            self.log("❌ Cannot proceed without login", "ERROR")
            return results
        
        # Test 2: Update PayPal Account
        results['update_paypal'] = self.update_paypal_account()
        
        # Test 3: Verify PayPal was saved
        results['verify_paypal_saved'] = self.verify_paypal_saved()
        
        # Test 4: Delete PayPal Account
        results['delete_paypal'] = self.delete_paypal_account()
        
        # Test 5: Verify PayPal deletion
        results['verify_paypal_deleted'] = self.verify_paypal_deleted()
        
        # Test 6: Prize Pool endpoint
        results['prize_pool_has_paypal'] = self.test_prize_pool_endpoint()
        
        # Test 7 & 8: Old PIX endpoints removed
        results['old_pix_endpoints_removed'] = self.test_old_pix_endpoints_removed()
        
        return results
    
    def print_summary(self, results: Dict[str, bool]):
        """Print test summary"""
        self.log("\n" + "="*50)
        self.log("📊 TEST SUMMARY")
        self.log("="*50)
        
        total_tests = len(results)
        passed_tests = sum(1 for result in results.values() if result)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            self.log(f"{test_name}: {status}")
        
        self.log(f"\nTotal: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            self.log("🎉 ALL TESTS PASSED - PayPal migration successful!")
        else:
            self.log("⚠️  SOME TESTS FAILED - PayPal migration needs attention")

def main():
    """Main test execution"""
    tester = PayPalRewardsTest()
    results = tester.run_all_tests()
    tester.print_summary(results)
    
    # Exit with error code if any tests failed
    if not all(results.values()):
        sys.exit(1)

if __name__ == "__main__":
    main()