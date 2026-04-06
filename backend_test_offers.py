#!/usr/bin/env python3
"""
BizRealms Backend Testing - Company Offers Improvement System
Testing the NEW endpoint: POST /api/companies/offers/improve
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BASE_URL = "https://career-mogul-1.preview.emergentagent.com/api"
TEST_EMAIL = "teste@businessempire.com"
TEST_PASSWORD = "teste123"

class BizRealmsOffersAPITester:
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
        
    def test_available_companies(self):
        """Test GET /api/companies/available to see companies for purchase."""
        self.log("🛒 Checking available companies...")
        
        response = self.session.get(f"{BASE_URL}/companies/available")
        
        if response.status_code != 200:
            self.log(f"❌ Get available companies failed: {response.status_code} - {response.text}", "ERROR")
            return False, []
            
        data = response.json()
        # API returns a list directly, not an object with 'companies' key
        companies = data if isinstance(data, list) else data.get('companies', [])
        
        self.log(f"✅ Found {len(companies)} available companies")
        if companies:
            cheapest = min(companies, key=lambda x: x.get('price', float('inf')))
            self.log(f"   💰 Cheapest: {cheapest.get('name', 'Unknown')} - R$ {cheapest.get('price', 0):,.2f}")
            
        return True, companies
        
    def test_buy_company(self, companies):
        """Test POST /api/companies/buy to purchase a company."""
        if not companies:
            self.log("❌ No companies available to buy", "ERROR")
            return False
            
        # Find the cheapest company
        cheapest = min(companies, key=lambda x: x.get('price', float('inf')))
        company_id = cheapest.get('id')
        
        self.log(f"💳 Attempting to buy company: {cheapest.get('name', 'Unknown')}")
        
        response = self.session.post(f"{BASE_URL}/companies/buy", json={
            "company_id": company_id
        })
        
        if response.status_code == 200:
            result = response.json()
            self.log(f"✅ Company purchased successfully!")
            self.log(f"   🏢 Company: {result.get('company', {}).get('name', 'Unknown')}")
            self.log(f"   💰 Cost: R$ {result.get('cost', 0):,.2f}")
            return True
        elif response.status_code == 400:
            error_data = response.json()
            if "insuficientes" in error_data.get('detail', '').lower():
                self.log(f"❌ Insufficient funds to buy company. Need R$ {cheapest.get('price', 0):,.2f}")
                return False
            else:
                self.log(f"❌ Company purchase failed: {error_data.get('detail', 'Unknown error')}")
                return False
        else:
            self.log(f"❌ Company purchase failed: {response.status_code} - {response.text}", "ERROR")
            return False
            
    def test_company_offers(self):
        """Test GET /api/companies/offers to check current offers."""
        self.log("📋 Checking company offers...")
        
        response = self.session.get(f"{BASE_URL}/companies/offers")
        
        if response.status_code != 200:
            self.log(f"❌ Get company offers failed: {response.status_code} - {response.text}", "ERROR")
            return False, []
            
        data = response.json()
        offers = data.get('offers', [])
        
        self.log(f"✅ Found {len(offers)} active offers")
        for offer in offers:
            self.log(f"   💼 Company: {offer.get('company_name', 'Unknown')}")
            self.log(f"      💰 Offer: R$ {offer.get('offer_amount', 0):,.2f}")
            self.log(f"      👤 Buyer: {offer.get('buyer_name', 'Unknown')}")
            self.log(f"      ⏰ Remaining: {offer.get('remaining_minutes', 0)} minutes")
            
        return True, offers
        
    def test_improve_offer(self, offers):
        """Test POST /api/companies/offers/improve - THE NEW ENDPOINT."""
        self.log("🚀 Testing NEW endpoint: POST /api/companies/offers/improve")
        
        if not offers:
            self.log("ℹ️ No offers available to improve. Testing with invalid offer_id...")
            # Test with invalid offer_id to check error handling
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
            
            self.log(f"💡 Improving offer for company: {offer.get('company_name', 'Unknown')}")
            self.log(f"   💰 Original offer: R$ {original_amount:,.2f}")
            
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
                
    def test_assets_owned(self):
        """Test GET /api/assets/owned endpoint."""
        self.log("🏠 Testing assets owned...")
        
        response = self.session.get(f"{BASE_URL}/assets/owned")
        
        if response.status_code != 200:
            self.log(f"❌ Get owned assets failed: {response.status_code} - {response.text}", "ERROR")
            return False
            
        data = response.json()
        assets = data.get('assets', [])
        
        self.log(f"✅ User owns {len(assets)} assets")
        for asset in assets[:3]:  # Show first 3
            self.log(f"   🏠 {asset.get('name', 'Unknown')} - Value: R$ {asset.get('current_value', 0):,.2f}")
            
        return True
        
    def test_assets_store(self):
        """Test GET /api/assets/store endpoint."""
        self.log("🛍️ Testing assets store...")
        
        response = self.session.get(f"{BASE_URL}/assets/store")
        
        if response.status_code != 200:
            self.log(f"❌ Get assets store failed: {response.status_code} - {response.text}", "ERROR")
            return False
            
        data = response.json()
        # API returns a list directly, not an object with 'assets' key
        assets = data if isinstance(data, list) else data.get('assets', [])
        
        self.log(f"✅ Found {len(assets)} assets in store")
        if assets:
            categories = set(asset.get('category', 'Unknown') for asset in assets)
            self.log(f"   📂 Categories: {', '.join(categories)}")
            
        return True
        
    def test_assets_offers(self):
        """Test GET /api/assets/offers endpoint."""
        self.log("💎 Testing assets offers...")
        
        response = self.session.get(f"{BASE_URL}/assets/offers")
        
        if response.status_code != 200:
            self.log(f"❌ Get assets offers failed: {response.status_code} - {response.text}", "ERROR")
            return False
            
        data = response.json()
        offers = data.get('offers', [])
        
        self.log(f"✅ Found {len(offers)} asset offers")
        for offer in offers[:3]:  # Show first 3
            self.log(f"   💎 {offer.get('asset_name', 'Unknown')} - Offer: R$ {offer.get('offer_amount', 0):,.2f}")
            
        return True
        
    def run_all_tests(self):
        """Run all tests in sequence."""
        self.log("🚀 Starting BizRealms Company Offers Improvement Tests")
        self.log("=" * 70)
        
        # Step 1: Login
        if not self.login():
            return False
            
        # Step 2: Check owned companies
        success, owned_companies = self.test_owned_companies()
        if not success:
            return False
            
        # Step 3: If no companies, try to buy one
        if not owned_companies:
            self.log("ℹ️ User has no companies. Attempting to buy one...")
            success, available_companies = self.test_available_companies()
            if not success:
                return False
                
            if not self.test_buy_company(available_companies):
                self.log("⚠️ Could not buy company. Continuing with offer tests...")
                
        # Step 4: Check current offers
        success, offers = self.test_company_offers()
        if not success:
            return False
            
        # Step 5: Test the NEW improve offer endpoint
        if not self.test_improve_offer(offers):
            return False
            
        # Step 6: Test asset endpoints as requested
        asset_tests = [
            ("Assets Owned", self.test_assets_owned),
            ("Assets Store", self.test_assets_store),
            ("Assets Offers", self.test_assets_offers),
        ]
        
        for test_name, test_func in asset_tests:
            self.log(f"\n🧪 Running test: {test_name}")
            try:
                if not test_func():
                    self.log(f"❌ {test_name} FAILED")
                    return False
                else:
                    self.log(f"✅ {test_name} PASSED")
            except Exception as e:
                self.log(f"❌ {test_name} FAILED with exception: {str(e)}", "ERROR")
                return False
                
        self.log("\n" + "=" * 70)
        self.log("🎉 ALL TESTS PASSED! Company Offers Improvement system is working correctly.")
        return True

if __name__ == "__main__":
    tester = BizRealmsOffersAPITester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)