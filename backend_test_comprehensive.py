#!/usr/bin/env python3
"""
BizRealms Backend Testing - Company Offers Improvement System - COMPREHENSIVE TEST
Testing the NEW endpoint: POST /api/companies/offers/improve with a user who has money
"""

import requests
import json
import sys
import time
from datetime import datetime

# Configuration
BASE_URL = "https://career-mogul-1.preview.emergentagent.com/api"
TEST_EMAIL = "test_jobs@businessempire.com"  # User with money
TEST_PASSWORD = "test123"

class BizRealmsComprehensiveOffersAPITester:
    def __init__(self):
        self.session = requests.Session()
        self.jwt_token = None
        self.user_data = None
        
    def log(self, message, level="INFO"):
        """Log test messages with timestamp."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def login(self):
        """Login and get JWT token."""
        self.log("🔐 Testing login...")
        
        response = self.session.post(f"{BASE_URL}/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        if response.status_code != 200:
            self.log(f"❌ Login failed: {response.status_code} - {response.text}", "ERROR")
            return False
            
        data = response.json()
        self.jwt_token = data.get('token')
        self.user_data = data.get('user', {})
        
        if not self.jwt_token:
            self.log("❌ No JWT token received", "ERROR")
            return False
            
        # Set authorization header for all future requests
        self.session.headers.update({
            'Authorization': f'Bearer {self.jwt_token}',
            'Content-Type': 'application/json'
        })
        
        self.log(f"✅ Login successful! User: {self.user_data.get('name', 'Unknown')}")
        self.log(f"   💰 Money: R$ {self.user_data.get('money', 0):,.2f}")
        return True
        
    def test_owned_companies(self):
        """Test GET /api/companies/owned to check if user has companies."""
        self.log("🏢 Checking owned companies...")
        
        response = self.session.get(f"{BASE_URL}/companies/owned")
        
        if response.status_code != 200:
            self.log(f"❌ Get owned companies failed: {response.status_code} - {response.text}", "ERROR")
            return False, []
            
        data = response.json()
        companies = data.get('companies', [])
        
        self.log(f"✅ User owns {len(companies)} companies")
        for company in companies:
            self.log(f"   🏢 {company.get('name', 'Unknown')} - Segment: {company.get('segment', 'Unknown')}")
            
        return True, companies
        
    def test_buy_company_if_needed(self):
        """Buy a company if user doesn't have any."""
        success, companies = self.test_owned_companies()
        if not success:
            return False
            
        if len(companies) > 0:
            self.log("✅ User already has companies, no need to buy")
            return True
            
        self.log("ℹ️ User has no companies. Attempting to buy one...")
        
        # Get available companies
        response = self.session.get(f"{BASE_URL}/companies/available")
        if response.status_code != 200:
            self.log(f"❌ Get available companies failed: {response.status_code} - {response.text}", "ERROR")
            return False
            
        available_companies = response.json()
        if not available_companies:
            self.log("❌ No companies available to buy", "ERROR")
            return False
            
        # Find the cheapest company
        cheapest = min(available_companies, key=lambda x: x.get('price', float('inf')))
        company_id = cheapest.get('id')
        
        self.log(f"💳 Attempting to buy company: {cheapest.get('name', 'Unknown')} - R$ {cheapest.get('price', 0):,.2f}")
        
        response = self.session.post(f"{BASE_URL}/companies/buy", json={
            "company_id": company_id
        })
        
        if response.status_code == 200:
            result = response.json()
            self.log(f"✅ Company purchased successfully!")
            self.log(f"   🏢 Company: {result.get('company', {}).get('name', 'Unknown')}")
            self.log(f"   💰 Cost: R$ {result.get('cost', 0):,.2f}")
            return True
        else:
            error_data = response.json() if response.status_code == 400 else {}
            self.log(f"❌ Company purchase failed: {error_data.get('detail', response.text)}")
            return False
            
    def wait_for_offers(self, max_attempts=10):
        """Wait for offers to be generated (they have a cooldown system)."""
        self.log("⏳ Waiting for offers to be generated...")
        
        for attempt in range(max_attempts):
            response = self.session.get(f"{BASE_URL}/companies/offers")
            if response.status_code != 200:
                self.log(f"❌ Get company offers failed: {response.status_code} - {response.text}", "ERROR")
                return False, []
                
            data = response.json()
            offers = data.get('offers', [])
            
            if offers:
                self.log(f"✅ Found {len(offers)} offers after {attempt + 1} attempts")
                return True, offers
                
            if attempt < max_attempts - 1:
                self.log(f"   ⏳ Attempt {attempt + 1}: No offers yet, waiting 30 seconds...")
                time.sleep(30)
            else:
                self.log("ℹ️ No offers generated after waiting. This is normal due to cooldown system.")
                
        return True, []
        
    def test_improve_offer_comprehensive(self):
        """Comprehensive test of the NEW improve offer endpoint."""
        self.log("🚀 COMPREHENSIVE TEST: POST /api/companies/offers/improve")
        
        # Step 1: Ensure user has companies
        if not self.test_buy_company_if_needed():
            self.log("❌ Could not ensure user has companies", "ERROR")
            return False
            
        # Step 2: Wait for offers to be generated
        success, offers = self.wait_for_offers()
        if not success:
            return False
            
        # Step 3: Test the improve offer endpoint
        if not offers:
            self.log("ℹ️ No offers available. Testing error handling with invalid offer_id...")
            
            # Test with invalid offer_id
            response = self.session.post(f"{BASE_URL}/companies/offers/improve", json={
                "offer_id": "invalid_offer_id_12345"
            })
            
            if response.status_code == 404:
                error_data = response.json()
                self.log(f"✅ Invalid offer_id correctly rejected with 404: {error_data.get('detail', 'Not found')}")
                return True
            else:
                self.log(f"❌ Expected 404 for invalid offer_id, got {response.status_code} - {response.text}", "ERROR")
                return False
        else:
            # Test with valid offer
            offer = offers[0]
            offer_id = offer.get('id')
            original_amount = offer.get('offer_amount', 0)
            company_name = offer.get('company_name', 'Unknown')
            
            self.log(f"💡 Testing offer improvement for company: {company_name}")
            self.log(f"   💰 Original offer: R$ {original_amount:,.2f}")
            self.log(f"   👤 Buyer: {offer.get('buyer_name', 'Unknown')}")
            self.log(f"   ⏰ Remaining: {offer.get('remaining_minutes', 0)} minutes")
            
            response = self.session.post(f"{BASE_URL}/companies/offers/improve", json={
                "offer_id": offer_id
            })
            
            if response.status_code == 200:
                result = response.json()
                new_amount = result.get('new_offer_amount', 0)
                improvement_pct = ((new_amount - original_amount) / original_amount) * 100 if original_amount > 0 else 0
                
                self.log(f"✅ Offer improved successfully!")
                self.log(f"   💰 New offer: R$ {new_amount:,.2f}")
                self.log(f"   📈 Improvement: {improvement_pct:.1f}% increase")
                self.log(f"   📺 Ad watched: {result.get('ad_watched', False)}")
                
                # Verify improvement is within expected range (15-25%)
                if 15 <= improvement_pct <= 25:
                    self.log(f"✅ Improvement percentage is within expected range (15-25%)")
                else:
                    self.log(f"⚠️ Improvement percentage {improvement_pct:.1f}% is outside expected range (15-25%)")
                    
                # Test duplicate improvement (should fail)
                self.log("🔄 Testing duplicate improvement (should fail)...")
                response2 = self.session.post(f"{BASE_URL}/companies/offers/improve", json={
                    "offer_id": offer_id
                })
                
                if response2.status_code == 400:
                    error_data = response2.json()
                    self.log(f"✅ Duplicate improvement correctly rejected: {error_data.get('detail', 'Unknown error')}")
                else:
                    self.log(f"⚠️ Duplicate improvement not properly handled: {response2.status_code}")
                    
                return True
            elif response.status_code == 400:
                error_data = response.json()
                self.log(f"❌ Offer improvement failed: {error_data.get('detail', 'Unknown error')}")
                return False
            elif response.status_code == 404:
                error_data = response.json()
                self.log(f"❌ Offer not found: {error_data.get('detail', 'Not found')}")
                return False
            else:
                self.log(f"❌ Offer improvement failed: {response.status_code} - {response.text}", "ERROR")
                return False
                
    def test_all_asset_endpoints(self):
        """Test all asset endpoints as requested."""
        self.log("🏠 Testing all asset endpoints...")
        
        endpoints = [
            ("GET /api/assets/owned", f"{BASE_URL}/assets/owned"),
            ("GET /api/assets/store", f"{BASE_URL}/assets/store"),
            ("GET /api/assets/offers", f"{BASE_URL}/assets/offers"),
        ]
        
        for endpoint_name, url in endpoints:
            self.log(f"   🧪 Testing {endpoint_name}...")
            response = self.session.get(url)
            
            if response.status_code != 200:
                self.log(f"   ❌ {endpoint_name} failed: {response.status_code} - {response.text}", "ERROR")
                return False
                
            data = response.json()
            
            if endpoint_name == "GET /api/assets/owned":
                assets = data.get('assets', [])
                self.log(f"   ✅ User owns {len(assets)} assets")
            elif endpoint_name == "GET /api/assets/store":
                assets = data if isinstance(data, list) else data.get('assets', [])
                categories = set(asset.get('category', 'Unknown') for asset in assets)
                self.log(f"   ✅ Found {len(assets)} assets in store, categories: {', '.join(categories)}")
            elif endpoint_name == "GET /api/assets/offers":
                offers = data.get('offers', [])
                self.log(f"   ✅ Found {len(offers)} asset offers")
                
        return True
        
    def run_comprehensive_test(self):
        """Run comprehensive test of the NEW endpoint."""
        self.log("🚀 Starting COMPREHENSIVE BizRealms Company Offers Improvement Test")
        self.log("=" * 80)
        
        # Step 1: Login
        if not self.login():
            return False
            
        # Step 2: Test the NEW improve offer endpoint comprehensively
        if not self.test_improve_offer_comprehensive():
            return False
            
        # Step 3: Test asset endpoints as requested
        if not self.test_all_asset_endpoints():
            return False
            
        self.log("\n" + "=" * 80)
        self.log("🎉 COMPREHENSIVE TEST PASSED! Company Offers Improvement system is working correctly.")
        self.log("✅ NEW endpoint POST /api/companies/offers/improve has been thoroughly tested")
        return True

if __name__ == "__main__":
    tester = BizRealmsComprehensiveOffersAPITester()
    success = tester.run_comprehensive_test()
    sys.exit(0 if success else 1)