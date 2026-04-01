#!/usr/bin/env python3
"""
Backend API Testing for Business Empire Game - NEW Endpoints
Testing the specific endpoints mentioned in the review request
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "https://career-mogul-1.preview.emergentagent.com/api"
TEST_EMAIL = "teste@businessempire.com"
TEST_PASSWORD = "teste123"

class BusinessEmpireAPITester:
    def __init__(self):
        self.base_url = BASE_URL
        self.token = None
        self.user_data = None
        
    def login(self):
        """Login and get JWT token"""
        print("🔐 Logging in...")
        response = requests.post(f"{self.base_url}/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        if response.status_code == 200:
            data = response.json()
            self.token = data['token']
            self.user_data = data['user']
            print(f"✅ Login successful! User: {self.user_data.get('name', 'Unknown')}")
            print(f"   Level: {self.user_data.get('level', 1)}, Money: R$ {self.user_data.get('money', 0):,.2f}")
            return True
        else:
            print(f"❌ Login failed: {response.status_code} - {response.text}")
            return False
    
    def get_headers(self):
        """Get headers with authorization"""
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def test_personal_data_endpoints(self):
        """Test Personal Data (Profile) endpoints"""
        print("\n" + "="*60)
        print("🧑‍💼 TESTING PERSONAL DATA ENDPOINTS")
        print("="*60)
        
        # Test PUT /api/user/personal-data
        print("\n📝 Testing PUT /api/user/personal-data...")
        personal_data = {
            "full_name": "Teste Jogador",
            "address": "Rua ABC 123",
            "city": "São Paulo",
            "state": "SP",
            "zip_code": "01000-000",
            "phone": "11999999999"
        }
        
        response = requests.put(
            f"{self.base_url}/user/personal-data",
            json=personal_data,
            headers=self.get_headers()
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Personal data updated successfully!")
            print(f"   Updated fields: {result.get('updated_fields', [])}")
        else:
            print(f"❌ Personal data update failed: {response.status_code} - {response.text}")
        
        # Test GET /api/user/me to verify new fields
        print("\n👤 Testing GET /api/user/me (verify new fields)...")
        response = requests.get(
            f"{self.base_url}/user/me",
            headers=self.get_headers()
        )
        
        if response.status_code == 200:
            user = response.json()
            print(f"✅ User profile retrieved successfully!")
            print(f"   Full Name: {user.get('full_name', 'Not set')}")
            print(f"   Address: {user.get('address', 'Not set')}")
            print(f"   City: {user.get('city', 'Not set')}")
            print(f"   State: {user.get('state', 'Not set')}")
            print(f"   ZIP Code: {user.get('zip_code', 'Not set')}")
            print(f"   Phone: {user.get('phone', 'Not set')}")
            
            # Verify all fields were saved
            expected_fields = ['full_name', 'address', 'city', 'state', 'zip_code', 'phone']
            missing_fields = [field for field in expected_fields if not user.get(field)]
            if missing_fields:
                print(f"⚠️  Missing fields: {missing_fields}")
            else:
                print("✅ All personal data fields present!")
        else:
            print(f"❌ Get user profile failed: {response.status_code} - {response.text}")
    
    def test_daily_reward_endpoints(self):
        """Test Daily Free Money endpoints"""
        print("\n" + "="*60)
        print("💰 TESTING DAILY REWARD ENDPOINTS")
        print("="*60)
        
        # Test GET /api/store/daily-reward-status (should be available first time)
        print("\n🎯 Testing GET /api/store/daily-reward-status (initial check)...")
        response = requests.get(
            f"{self.base_url}/store/daily-reward-status",
            headers=self.get_headers()
        )
        
        if response.status_code == 200:
            status = response.json()
            print(f"✅ Daily reward status retrieved!")
            print(f"   Available: {status.get('available', False)}")
            print(f"   Already claimed: {status.get('already_claimed', False)}")
            print(f"   Reward amount: R$ {status.get('reward_amount', 0):,.0f}")
            
            initial_available = status.get('available', False)
        else:
            print(f"❌ Daily reward status failed: {response.status_code} - {response.text}")
            return
        
        # Test POST /api/store/daily-reward (claim reward)
        print("\n🎁 Testing POST /api/store/daily-reward (claim reward)...")
        response = requests.post(
            f"{self.base_url}/store/daily-reward",
            headers=self.get_headers()
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Daily reward claimed successfully!")
            print(f"   Message: {result.get('message', '')}")
            print(f"   Amount: R$ {result.get('amount', 0):,.0f}")
            print(f"   New balance: R$ {result.get('new_balance', 0):,.2f}")
            print(f"   Level bonus: R$ {result.get('level_bonus', 0):,.0f}")
        else:
            print(f"❌ Daily reward claim failed: {response.status_code} - {response.text}")
        
        # Test GET /api/store/daily-reward-status (should now be unavailable)
        print("\n🚫 Testing GET /api/store/daily-reward-status (after claim)...")
        response = requests.get(
            f"{self.base_url}/store/daily-reward-status",
            headers=self.get_headers()
        )
        
        if response.status_code == 200:
            status = response.json()
            print(f"✅ Daily reward status retrieved!")
            print(f"   Available: {status.get('available', False)}")
            print(f"   Already claimed: {status.get('already_claimed', False)}")
            
            if not status.get('available', True):
                print("✅ Reward correctly marked as unavailable after claiming!")
            else:
                print("⚠️  Reward still shows as available after claiming!")
        else:
            print(f"❌ Daily reward status failed: {response.status_code} - {response.text}")
        
        # Test POST /api/store/daily-reward again (should fail with 400)
        print("\n🔄 Testing POST /api/store/daily-reward (duplicate claim - should fail)...")
        response = requests.post(
            f"{self.base_url}/store/daily-reward",
            headers=self.get_headers()
        )
        
        if response.status_code == 400:
            print(f"✅ Duplicate claim correctly rejected!")
            print(f"   Error message: {response.json().get('detail', 'No detail')}")
        else:
            print(f"⚠️  Expected 400 error, got: {response.status_code} - {response.text}")
    
    def test_higher_level_jobs_endpoint(self):
        """Test Higher-Level Jobs endpoint"""
        print("\n" + "="*60)
        print("💼 TESTING HIGHER-LEVEL JOBS ENDPOINT")
        print("="*60)
        
        # Test GET /api/jobs/available-for-level
        print("\n🎯 Testing GET /api/jobs/available-for-level...")
        response = requests.get(
            f"{self.base_url}/jobs/available-for-level",
            headers=self.get_headers()
        )
        
        if response.status_code == 200:
            jobs = response.json()
            print(f"✅ Jobs for level retrieved successfully!")
            print(f"   Total jobs available: {len(jobs)}")
            
            # Count base jobs vs higher-level jobs
            base_jobs = [j for j in jobs if not j.get('is_premium', False)]
            premium_jobs = [j for j in jobs if j.get('is_premium', False)]
            
            print(f"   Base jobs: {len(base_jobs)}")
            print(f"   Higher-level jobs: {len(premium_jobs)}")
            
            if premium_jobs:
                print("\n🌟 Higher-level jobs available:")
                for job in premium_jobs[:3]:  # Show first 3
                    print(f"   • {job.get('title', 'Unknown')} at {job.get('company', 'Unknown')}")
                    print(f"     Salary: R$ {job.get('salary', 0):,.0f}/month")
                    print(f"     Min Level: {job.get('min_level', 1)}")
            else:
                print("   No higher-level jobs available for current user level")
                
            # Verify structure
            if jobs:
                sample_job = jobs[0]
                required_fields = ['id', 'title', 'company', 'description', 'salary', 'location', 'requirements', 'status']
                missing_fields = [field for field in required_fields if field not in sample_job]
                if missing_fields:
                    print(f"⚠️  Missing required fields in job: {missing_fields}")
                else:
                    print("✅ Job structure validation passed!")
        else:
            print(f"❌ Higher-level jobs request failed: {response.status_code} - {response.text}")
    
    def test_franchise_system_endpoint(self):
        """Test Franchise System endpoint"""
        print("\n" + "="*60)
        print("🏢 TESTING FRANCHISE SYSTEM ENDPOINT")
        print("="*60)
        
        # First, check if user has any companies
        print("\n🔍 Checking user's companies...")
        response = requests.get(
            f"{self.base_url}/companies/owned",
            headers=self.get_headers()
        )
        
        eligible_company = None
        if response.status_code == 200:
            companies = response.json()
            print(f"   User owns {len(companies)} companies")
            
            # Look for eligible companies (restaurante, loja, fabrica)
            eligible_segments = ['restaurante', 'loja', 'fabrica']
            for company in companies:
                if isinstance(company, dict) and company.get('segment') in eligible_segments:
                    eligible_company = company
                    print(f"   Found eligible company: {company.get('name')} ({company.get('segment')})")
                    break
        
        # Test POST /api/companies/create-franchise
        print("\n🏪 Testing POST /api/companies/create-franchise...")
        
        if eligible_company:
            franchise_data = {
                "company_id": eligible_company['id'],
                "franchise_name": "Franquia Teste",
                "franchise_location": "Shopping Center ABC"
            }
            
            response = requests.post(
                f"{self.base_url}/companies/create-franchise",
                json=franchise_data,
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Franchise created successfully!")
                print(f"   Message: {result.get('message', '')}")
                print(f"   Franchise name: {result.get('franchise', {}).get('name', 'Unknown')}")
                print(f"   Cost: R$ {result.get('cost', 0):,.0f}")
                print(f"   Monthly revenue: R$ {result.get('monthly_revenue', 0):,.0f}")
                print(f"   New balance: R$ {result.get('new_balance', 0):,.2f}")
            elif response.status_code == 400:
                error_detail = response.json().get('detail', 'Unknown error')
                if "Saldo insuficiente" in error_detail:
                    print(f"⚠️  Insufficient funds for franchise creation: {error_detail}")
                elif "Limite de" in error_detail:
                    print(f"⚠️  Franchise limit reached: {error_detail}")
                else:
                    print(f"⚠️  Franchise creation failed: {error_detail}")
            else:
                print(f"❌ Franchise creation failed: {response.status_code} - {response.text}")
        else:
            # Test with non-eligible company or no company
            print("   No eligible company found. Testing error message for ineligible segment...")
            
            # Try with a fake company ID to test error handling
            franchise_data = {
                "company_id": "fake-company-id",
                "franchise_name": "Test Franchise",
                "franchise_location": "Test Location"
            }
            
            response = requests.post(
                f"{self.base_url}/companies/create-franchise",
                json=franchise_data,
                headers=self.get_headers()
            )
            
            if response.status_code == 404:
                print(f"✅ Correctly rejected non-existent company: {response.json().get('detail', '')}")
            else:
                print(f"⚠️  Expected 404 for non-existent company, got: {response.status_code} - {response.text}")
    
    def test_market_events_endpoints(self):
        """Test Market Events endpoints"""
        print("\n" + "="*60)
        print("📈 TESTING MARKET EVENTS ENDPOINTS")
        print("="*60)
        
        # Test GET /api/market/events (initial - may be empty)
        print("\n📊 Testing GET /api/market/events (initial check)...")
        response = requests.get(
            f"{self.base_url}/market/events",
            headers=self.get_headers()
        )
        
        if response.status_code == 200:
            events_data = response.json()
            initial_count = events_data.get('count', 0)
            print(f"✅ Market events retrieved successfully!")
            print(f"   Active events: {initial_count}")
            
            if initial_count > 0:
                print("   Current events:")
                for event in events_data.get('active_events', [])[:2]:  # Show first 2
                    print(f"   • {event.get('title', 'Unknown')}: {event.get('description', '')}")
                    print(f"     Duration: {event.get('seconds_remaining', 0)} seconds remaining")
        else:
            print(f"❌ Market events request failed: {response.status_code} - {response.text}")
            return
        
        # Test POST /api/market/trigger-event
        print("\n🎲 Testing POST /api/market/trigger-event...")
        response = requests.post(
            f"{self.base_url}/market/trigger-event",
            headers=self.get_headers()
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Market event triggered successfully!")
            event = result.get('event', {})
            print(f"   Event: {event.get('title', 'Unknown')}")
            print(f"   Description: {event.get('description', '')}")
            print(f"   Duration: {event.get('duration_hours', 0)} hours")
            print(f"   Effect: {event.get('effect', {})}")
        elif response.status_code == 400:
            error_detail = response.json().get('detail', 'Unknown error')
            if "Próximo evento em" in error_detail:
                print(f"⚠️  Event cooldown active: {error_detail}")
            else:
                print(f"⚠️  Event trigger failed: {error_detail}")
        else:
            print(f"❌ Event trigger failed: {response.status_code} - {response.text}")
        
        # Test GET /api/market/events again (should now have 1 active event)
        print("\n📈 Testing GET /api/market/events (after trigger)...")
        response = requests.get(
            f"{self.base_url}/market/events",
            headers=self.get_headers()
        )
        
        if response.status_code == 200:
            events_data = response.json()
            final_count = events_data.get('count', 0)
            print(f"✅ Market events retrieved successfully!")
            print(f"   Active events: {final_count}")
            
            if final_count > initial_count:
                print("✅ New event successfully added!")
            elif final_count == initial_count and initial_count > 0:
                print("⚠️  Event count unchanged (may be due to cooldown)")
            else:
                print("⚠️  Event count did not increase as expected")
        else:
            print(f"❌ Market events request failed: {response.status_code} - {response.text}")
        
        # Test POST /api/market/trigger-event again (should fail within 1 hour)
        print("\n🔄 Testing POST /api/market/trigger-event (duplicate - should fail)...")
        response = requests.post(
            f"{self.base_url}/market/trigger-event",
            headers=self.get_headers()
        )
        
        if response.status_code == 400:
            error_detail = response.json().get('detail', 'Unknown error')
            print(f"✅ Duplicate trigger correctly rejected: {error_detail}")
        else:
            print(f"⚠️  Expected 400 error for duplicate trigger, got: {response.status_code} - {response.text}")
    
    def test_asset_images_endpoints(self):
        """Test Asset Images endpoints"""
        print("\n" + "="*60)
        print("🖼️  TESTING ASSET IMAGES ENDPOINTS")
        print("="*60)
        
        # Test specific assets mentioned in review request
        test_assets = [
            ("moto_cg160", "Moto CG 160"),
            ("kitnet", "Kitnet"),
            ("rolex", "Rolex"),
            ("nonexistent", "Non-existent asset (should return defaults)")
        ]
        
        for asset_key, description in test_assets:
            print(f"\n🎨 Testing GET /api/assets/images/{asset_key} ({description})...")
            response = requests.get(f"{self.base_url}/assets/images/{asset_key}")
            
            if response.status_code == 200:
                result = response.json()
                images = result.get('images', [])
                print(f"✅ Asset images retrieved successfully!")
                print(f"   Number of images: {len(images)}")
                
                if len(images) == 4:
                    print("✅ Correct number of images (4) returned!")
                else:
                    print(f"⚠️  Expected 4 images, got {len(images)}")
                
                # Show first 2 image URLs
                for i, img_url in enumerate(images[:2]):
                    print(f"   Image {i+1}: {img_url}")
                
                # Verify URLs are valid
                valid_urls = all(url.startswith('https://') for url in images)
                if valid_urls:
                    print("✅ All image URLs are valid HTTPS URLs!")
                else:
                    print("⚠️  Some image URLs are not valid HTTPS URLs")
            else:
                print(f"❌ Asset images request failed: {response.status_code} - {response.text}")
    
    def run_all_tests(self):
        """Run all NEW endpoint tests"""
        print("🚀 STARTING BUSINESS EMPIRE NEW ENDPOINTS TESTING")
        print("="*80)
        print(f"Backend URL: {self.base_url}")
        print(f"Test User: {TEST_EMAIL}")
        print("="*80)
        
        # Login first
        if not self.login():
            print("❌ Cannot proceed without login!")
            return
        
        # Run all tests
        try:
            self.test_personal_data_endpoints()
            self.test_daily_reward_endpoints()
            self.test_higher_level_jobs_endpoint()
            self.test_franchise_system_endpoint()
            self.test_market_events_endpoints()
            self.test_asset_images_endpoints()
            
            print("\n" + "="*80)
            print("🎉 ALL NEW ENDPOINT TESTS COMPLETED!")
            print("="*80)
            
        except Exception as e:
            print(f"\n❌ Test execution failed with error: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    tester = BusinessEmpireAPITester()
    tester.run_all_tests()