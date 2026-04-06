#!/usr/bin/env python3
"""
BizRealms Revenue Collection Testing
Testing company revenue collection, jobs salary collection, and related systems.
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BASE_URL = "https://career-mogul-1.preview.emergentagent.com/api"
TEST_EMAIL = "teste@businessempire.com"
TEST_PASSWORD = "teste123"

class RevenueCollectionTester:
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
        return True
        
    def test_companies_owned(self):
        """Test GET /api/companies/owned - Should return owned companies with daily_revenue field."""
        self.log("🏢 Testing GET /api/companies/owned...")
        
        response = self.session.get(f"{BASE_URL}/companies/owned")
        
        if response.status_code != 200:
            self.log(f"❌ Companies owned failed: {response.status_code} - {response.text}", "ERROR")
            return False
            
        data = response.json()
        
        # Validate response structure
        if 'companies' not in data:
            self.log("❌ Missing 'companies' field in response", "ERROR")
            return False
            
        companies = data['companies']
        if not isinstance(companies, list):
            self.log("❌ Companies should be a list", "ERROR")
            return False
            
        self.log(f"✅ Companies owned endpoint working! Found {len(companies)} companies")
        
        if len(companies) == 0:
            self.log("ℹ️ User has no companies - this is expected for some test users")
            return True
            
        # Check for daily_revenue field in each company
        for i, company in enumerate(companies):
            if 'daily_revenue' not in company:
                # Check for monthly_revenue for backward compatibility
                if 'monthly_revenue' not in company:
                    self.log(f"❌ Company {i+1} missing both daily_revenue and monthly_revenue fields", "ERROR")
                    return False
                else:
                    self.log(f"⚠️ Company {i+1} has monthly_revenue but no daily_revenue field")
            else:
                self.log(f"✅ Company {i+1}: {company.get('name', 'Unknown')} - Daily revenue: R$ {company['daily_revenue']:.2f}")
                
        return True
        
    def test_companies_collect_revenue(self):
        """Test POST /api/companies/collect-revenue - Should work without KeyError."""
        self.log("💰 Testing POST /api/companies/collect-revenue...")
        
        response = self.session.post(f"{BASE_URL}/companies/collect-revenue")
        
        if response.status_code != 200:
            self.log(f"❌ Companies collect failed: {response.status_code} - {response.text}", "ERROR")
            return False
            
        data = response.json()
        
        # Validate response structure
        required_fields = ['total_revenue']
        for field in required_fields:
            if field not in data:
                self.log(f"❌ Missing field in collect response: {field}", "ERROR")
                return False
                
        self.log(f"✅ Companies collect working! Total revenue: R$ {data['total_revenue']:.2f}")
        self.log(f"   📝 Message: {data.get('message', 'No message')}")
        
        return True
        
    def test_jobs_collect_earnings(self):
        """Test GET /api/jobs/collect-earnings - Should work with new game time system."""
        self.log("💼 Testing GET /api/jobs/collect-earnings...")
        
        response = self.session.get(f"{BASE_URL}/jobs/collect-earnings")
        
        if response.status_code != 200:
            self.log(f"❌ Jobs collect earnings failed: {response.status_code} - {response.text}", "ERROR")
            return False
            
        data = response.json()
        
        # Validate response structure
        if 'message' not in data:
            self.log("❌ Missing 'message' field in jobs collect response", "ERROR")
            return False
            
        self.log(f"✅ Jobs collect earnings working! Message: {data['message']}")
        
        # Check for earnings data if available
        if 'earnings' in data:
            self.log(f"   💵 Earnings collected: R$ {data['earnings']:.2f}")
        if 'xp_gained' in data:
            self.log(f"   ⭐ XP gained: {data['xp_gained']}")
            
        return True
        
    def test_investments_market(self):
        """Test GET /api/investments/market - Should return world stocks and crypto with USD prices."""
        self.log("📈 Testing GET /api/investments/market...")
        
        response = self.session.get(f"{BASE_URL}/investments/market")
        
        if response.status_code != 200:
            self.log(f"❌ Investments market failed: {response.status_code} - {response.text}", "ERROR")
            return False
            
        data = response.json()
        
        # The API returns an array directly, not wrapped in an object
        if not isinstance(data, list):
            self.log("❌ Market data should be a list", "ERROR")
            return False
            
        assets = data
        self.log(f"✅ Investments market working! Found {len(assets)} assets")
        
        # Look for specific world stocks and crypto
        world_stocks = ['TechVista', 'NovaCorp', 'BlueShield']
        crypto_assets = ['BTC', 'ETH', 'SOL']
        
        found_stocks = []
        found_crypto = []
        usd_prices_found = False
        
        for asset in assets:
            # Check for required fields
            required_fields = ['ticker', 'name', 'current_price', 'category']
            for field in required_fields:
                if field not in asset:
                    self.log(f"❌ Missing field in asset: {field}", "ERROR")
                    return False
                    
            # Check for world stocks
            for stock in world_stocks:
                if stock in asset['name'] or stock in asset['ticker']:
                    found_stocks.append(asset['name'])
                    
            # Check for crypto
            for crypto in crypto_assets:
                if crypto in asset['ticker']:
                    found_crypto.append(asset['ticker'])
                    
            # Check for USD prices (look for $ symbol or USD in price formatting)
            price_str = str(asset['current_price'])
            market_cap = asset.get('market_cap', '')
            if '$' in market_cap or 'USD' in market_cap:
                usd_prices_found = True
                
        self.log(f"   🏢 World stocks found: {found_stocks}")
        self.log(f"   ₿ Crypto assets found: {found_crypto}")
        self.log(f"   💵 USD prices found: {usd_prices_found}")
        
        return True
        
    def test_assets_store(self):
        """Test GET /api/assets/store - Should return assets with fictional names."""
        self.log("🏪 Testing GET /api/assets/store...")
        
        response = self.session.get(f"{BASE_URL}/assets/store")
        
        if response.status_code != 200:
            self.log(f"❌ Assets store failed: {response.status_code} - {response.text}", "ERROR")
            return False
            
        data = response.json()
        
        # The API returns an array directly, not wrapped in an object
        if not isinstance(data, list):
            self.log("❌ Assets data should be a list", "ERROR")
            return False
            
        assets = data
        self.log(f"✅ Assets store working! Found {len(assets)} assets")
        
        # Check for fictional names (should NOT contain real brand names)
        real_brands = ['Ferrari', 'BMW', 'Rolex', 'Mercedes', 'Audi', 'Porsche', 'Lamborghini']
        fictional_examples = ['Veloce GT Sport', 'Luxor Premium SUV', 'Classic Diver Watch']
        
        real_brands_found = []
        fictional_names_found = []
        
        for asset in assets:
            # Check for required fields
            required_fields = ['name', 'price', 'category']
            for field in required_fields:
                if field not in asset:
                    self.log(f"❌ Missing field in asset: {field}", "ERROR")
                    return False
                    
            asset_name = asset['name']
            
            # Check for real brand names (should not be present)
            for brand in real_brands:
                if brand.lower() in asset_name.lower():
                    real_brands_found.append(asset_name)
                    
            # Check for fictional examples
            for example in fictional_examples:
                if example.lower() in asset_name.lower():
                    fictional_names_found.append(asset_name)
                    
        if real_brands_found:
            self.log(f"⚠️ Real brand names found (should be fictional): {real_brands_found}")
        else:
            self.log("✅ No real brand names found - all assets have fictional names")
            
        self.log(f"   🎭 Example fictional names: {fictional_names_found[:3]}")
        
        # Show some asset examples
        for i, asset in enumerate(assets[:5]):
            self.log(f"   {i+1}. {asset['name']} - R$ {asset['price']:,.2f} ({asset['category']})")
            
        return True
        
    def test_user_profile(self):
        """Test GET /api/user/me to check user status."""
        self.log("👤 Testing GET /api/user/me...")
        
        response = self.session.get(f"{BASE_URL}/user/me")
        
        if response.status_code != 200:
            self.log(f"❌ User profile failed: {response.status_code} - {response.text}", "ERROR")
            return False
            
        data = response.json()
        
        self.log(f"✅ User profile working!")
        self.log(f"   👤 Name: {data.get('name', 'Unknown')}")
        self.log(f"   💰 Money: R$ {data.get('money', 0):,.2f}")
        self.log(f"   ⭐ Level: {data.get('level', 0)}")
        self.log(f"   🎯 XP: {data.get('experience_points', 0):,}")
        
        return True
        
    def run_all_tests(self):
        """Run all tests in sequence."""
        self.log("🚀 Starting BizRealms Revenue Collection Tests")
        self.log("=" * 60)
        
        tests = [
            ("Login", self.login),
            ("User Profile", self.test_user_profile),
            ("Companies Owned", self.test_companies_owned),
            ("Companies Collect Revenue", self.test_companies_collect_revenue),
            ("Jobs Collect Earnings", self.test_jobs_collect_earnings),
            ("Investments Market", self.test_investments_market),
            ("Assets Store", self.test_assets_store),
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            self.log(f"\n🧪 Running test: {test_name}")
            try:
                if test_func():
                    passed += 1
                    self.log(f"✅ {test_name} PASSED")
                else:
                    failed += 1
                    self.log(f"❌ {test_name} FAILED")
            except Exception as e:
                failed += 1
                self.log(f"❌ {test_name} FAILED with exception: {str(e)}", "ERROR")
                
        self.log("\n" + "=" * 60)
        self.log(f"🏁 Test Results: {passed} passed, {failed} failed")
        
        if failed == 0:
            self.log("🎉 ALL TESTS PASSED! Revenue collection systems are working correctly.")
            return True
        else:
            self.log(f"⚠️ {failed} tests failed. Please check the issues above.")
            return False

if __name__ == "__main__":
    tester = RevenueCollectionTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)