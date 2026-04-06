#!/usr/bin/env python3
"""
Backend Testing Script for BizRealms New Features
Testing specific endpoints as requested in the review.
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BASE_URL = "https://career-mogul-1.preview.emergentagent.com/api"
TEST_EMAIL = "teste@businessempire.com"
TEST_PASSWORD = "teste123"

class BizRealmsNewFeaturesTester:
    def __init__(self):
        self.session = requests.Session()
        self.jwt_token = None
        self.user_id = None
        
    def log(self, message):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")
        
    def login(self):
        """Test login and get JWT token"""
        self.log("🔐 Testing Login...")
        
        login_data = {
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/auth/login", json=login_data)
            self.log(f"Login Response Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                self.jwt_token = data.get("token")
                user_data = data.get("user", {})
                self.user_id = user_data.get("id")
                
                # Set authorization header for future requests
                self.session.headers.update({
                    "Authorization": f"Bearer {self.jwt_token}"
                })
                
                self.log(f"✅ Login successful! User ID: {self.user_id}")
                return True
            else:
                self.log(f"❌ Login failed: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Login error: {str(e)}")
            return False
    
    def test_public_profile(self):
        """Test public profile endpoint with user's own ID"""
        self.log("👤 Testing Public Profile...")
        
        if not self.user_id:
            self.log("❌ No user ID available for public profile test")
            return False
        
        try:
            response = self.session.get(f"{BASE_URL}/user/profile/{self.user_id}")
            self.log(f"Public Profile Response Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"Public Profile Response: {json.dumps(data, indent=2)}")
                
                # Check required fields
                required_fields = [
                    "name", "level", "money", "companies_count", "assets_count", 
                    "investments_count", "education_count", "certification_count", 
                    "work_experience_count", "comparison"
                ]
                
                missing_fields = []
                for field in required_fields:
                    if field not in data:
                        missing_fields.append(field)
                
                if not missing_fields:
                    self.log("✅ All required fields present in public profile")
                    
                    # Check comparison object
                    comparison = data.get("comparison", {})
                    if "my_level" in comparison and "my_money" in comparison:
                        self.log("✅ Comparison object has my_level and my_money fields")
                        return True
                    else:
                        self.log("❌ Comparison object missing my_level or my_money")
                        return False
                else:
                    self.log(f"❌ Missing required fields: {missing_fields}")
                    return False
            else:
                self.log(f"❌ Public profile failed: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Public profile error: {str(e)}")
            return False
    
    def test_companies_offers(self):
        """Test companies offers endpoint"""
        self.log("🏢 Testing Companies Offers...")
        
        try:
            response = self.session.get(f"{BASE_URL}/companies/offers")
            self.log(f"Companies Offers Response Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"Companies Offers Response: {json.dumps(data, indent=2)}")
                
                # Check for offers array
                if "offers" in data:
                    offers = data["offers"]
                    self.log(f"✅ Offers array found with {len(offers)} offers")
                    return True
                else:
                    self.log("❌ Offers array missing from response")
                    self.log(f"Available fields: {list(data.keys())}")
                    return False
            else:
                self.log(f"❌ Companies offers failed with status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Companies offers error: {str(e)}")
            return False
    
    def test_user_stats_unique_jobs(self):
        """Test user stats endpoint for work_experience_count field"""
        self.log("📊 Testing User Stats - Unique Jobs...")
        
        try:
            response = self.session.get(f"{BASE_URL}/user/stats")
            self.log(f"User Stats Response Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"User Stats Response: {json.dumps(data, indent=2)}")
                
                # Check for work_experience_count field
                if "work_experience_count" in data:
                    count = data["work_experience_count"]
                    if isinstance(count, (int, float)):
                        self.log(f"✅ work_experience_count is a number: {count}")
                        return True
                    else:
                        self.log(f"❌ work_experience_count is not a number: {count} (type: {type(count)})")
                        return False
                else:
                    self.log("❌ work_experience_count field missing from response")
                    self.log(f"Available fields: {list(data.keys())}")
                    return False
            else:
                self.log(f"❌ User stats failed: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ User stats error: {str(e)}")
            return False
    
    def test_companies_owned_roi(self):
        """Test companies owned endpoint for ROI fields"""
        self.log("🏢 Testing Companies Owned with ROI...")
        
        try:
            response = self.session.get(f"{BASE_URL}/companies/owned")
            self.log(f"Companies Owned Response Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"Companies Owned Response: {json.dumps(data, indent=2)}")
                
                companies = data.get("companies", [])
                self.log(f"User owns {len(companies)} companies")
                
                # Check ROI fields in response structure
                roi_fields = ["roi_months", "roi_progress", "roi_recovered"]
                
                if len(companies) > 0:
                    # Check first company for ROI fields
                    company = companies[0]
                    missing_fields = []
                    
                    for field in roi_fields:
                        if field not in company:
                            missing_fields.append(field)
                    
                    if not missing_fields:
                        self.log(f"✅ All ROI fields present in company response")
                        for field in roi_fields:
                            self.log(f"  - {field}: {company[field]}")
                        return True
                    else:
                        self.log(f"❌ Missing ROI fields: {missing_fields}")
                        self.log(f"Available fields: {list(company.keys())}")
                        return False
                else:
                    self.log("ℹ️ User has no companies - checking response structure")
                    # Even with no companies, the endpoint should be well-formed
                    if "companies" in data:
                        self.log("✅ Companies endpoint response is well-formed (empty array)")
                        return True
                    else:
                        self.log("❌ Companies endpoint response malformed")
                        return False
                        
            else:
                self.log(f"❌ Companies owned failed: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Companies owned error: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all requested tests"""
        self.log("🚀 Starting BizRealms New Features Testing...")
        self.log("=" * 60)
        
        results = {}
        
        # Test 1: Login
        results["login"] = self.login()
        if not results["login"]:
            self.log("❌ Cannot proceed without login")
            return results
        
        # Test 2: Public Profile
        results["public_profile"] = self.test_public_profile()
        
        # Test 3: Companies Offers
        results["companies_offers"] = self.test_companies_offers()
        
        # Test 4: User Stats unique jobs
        results["user_stats_unique_jobs"] = self.test_user_stats_unique_jobs()
        
        # Test 5: Companies owned with ROI
        results["companies_owned_roi"] = self.test_companies_owned_roi()
        
        # Summary
        self.log("=" * 60)
        self.log("📋 TEST SUMMARY:")
        
        passed = 0
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            self.log(f"  {test_name}: {status}")
            if result:
                passed += 1
        
        self.log(f"\n🎯 Overall Result: {passed}/{total} tests passed")
        
        if passed == total:
            self.log("🎉 ALL NEW FEATURES TESTS PASSED!")
        else:
            self.log("⚠️ Some tests failed - see details above")
        
        return results

def main():
    """Main function"""
    tester = BizRealmsNewFeaturesTester()
    results = tester.run_all_tests()
    
    # Exit with appropriate code
    all_passed = all(results.values())
    sys.exit(0 if all_passed else 1)

if __name__ == "__main__":
    main()