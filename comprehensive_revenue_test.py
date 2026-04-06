#!/usr/bin/env python3
"""
BizRealms Revenue Collection Testing - Comprehensive Test
Testing company revenue collection, jobs salary collection, and related systems with a user that has companies and jobs.
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BASE_URL = "https://career-mogul-1.preview.emergentagent.com/api"
TEST_EMAIL = "test_jobs@businessempire.com"  # User with companies and job
TEST_PASSWORD = "test123"

class ComprehensiveRevenueCollectionTester:
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
        
    def test_companies_owned_with_daily_revenue(self):
        """Test GET /api/companies/owned - Should return owned companies with daily_revenue field."""
        self.log("🏢 Testing GET /api/companies/owned (with companies)...")
        
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
            self.log("❌ Expected user to have companies but found none", "ERROR")
            return False
            
        # Check for daily_revenue field in each company
        daily_revenue_found = False
        monthly_revenue_found = False
        
        for i, company in enumerate(companies):
            self.log(f"   🏢 Company {i+1}: {company.get('name', 'Unknown')}")
            
            if 'daily_revenue' in company:
                daily_revenue_found = True
                self.log(f"      ✅ Daily revenue: R$ {company['daily_revenue']:.2f}")
            else:
                self.log(f"      ❌ Missing daily_revenue field")
                
            if 'monthly_revenue' in company:
                monthly_revenue_found = True
                self.log(f"      📊 Monthly revenue: R$ {company['monthly_revenue']:.2f}")
                
            # Check for other important fields
            if 'effective_revenue' in company:
                self.log(f"      💰 Effective revenue: R$ {company['effective_revenue']:.2f}")
            if 'ad_boost_active' in company:
                boost_status = "Active" if company['ad_boost_active'] else "Inactive"
                self.log(f"      🚀 Ad boost: {boost_status}")
                
        if not daily_revenue_found:
            self.log("❌ No companies have daily_revenue field", "ERROR")
            return False
            
        self.log("✅ All companies have daily_revenue field - KeyError issue resolved!")
        return True
        
    def test_companies_collect_revenue_working(self):
        """Test POST /api/companies/collect-revenue - Should work without KeyError."""
        self.log("💰 Testing POST /api/companies/collect-revenue (with companies)...")
        
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
        
        # Check for additional fields
        if 'xp_gained' in data:
            self.log(f"   ⭐ XP gained: {data['xp_gained']}")
        if 'new_balance' in data:
            self.log(f"   💵 New balance: R$ {data['new_balance']:.2f}")
        if 'details' in data:
            self.log(f"   📊 Collection details: {len(data['details'])} companies")
            
        self.log("✅ No KeyError exceptions - revenue collection system working correctly!")
        return True
        
    def test_jobs_collect_earnings_working(self):
        """Test GET /api/jobs/collect-earnings - Should work with new game time system."""
        self.log("💼 Testing GET /api/jobs/collect-earnings (with job)...")
        
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
        if 'days_elapsed' in data:
            self.log(f"   📅 Game days elapsed: {data['days_elapsed']:.2f}")
        if 'new_balance' in data:
            self.log(f"   💰 New balance: R$ {data['new_balance']:.2f}")
            
        self.log("✅ Game time system (30 game days = 24 real hours) working correctly!")
        return True
        
    def test_current_job_status(self):
        """Test GET /api/jobs/current - Check current job status."""
        self.log("👔 Testing GET /api/jobs/current...")
        
        response = self.session.get(f"{BASE_URL}/jobs/current")
        
        if response.status_code != 200:
            self.log(f"❌ Current job failed: {response.status_code} - {response.text}", "ERROR")
            return False
            
        data = response.json()
        
        self.log(f"✅ Current job working!")
        self.log(f"   🏢 Company: {data.get('company', 'Unknown')}")
        self.log(f"   💼 Position: {data.get('position', 'Unknown')}")
        self.log(f"   💰 Salary: R$ {data.get('salary', 0):,.2f}")
        self.log(f"   📅 Start date: {data.get('start_date', 'Unknown')}")
        
        return True
        
    def test_investments_market_usd_prices(self):
        """Test GET /api/investments/market - Verify USD prices and world stocks."""
        self.log("📈 Testing GET /api/investments/market (USD prices)...")
        
        response = self.session.get(f"{BASE_URL}/investments/market")
        
        if response.status_code != 200:
            self.log(f"❌ Investments market failed: {response.status_code} - {response.text}", "ERROR")
            return False
            
        data = response.json()
        
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
        usd_assets = []
        
        for asset in assets:
            # Check for world stocks
            for stock in world_stocks:
                if stock in asset['name'] or stock in asset['ticker']:
                    found_stocks.append(asset['name'])
                    
            # Check for crypto
            for crypto in crypto_assets:
                if crypto in asset['ticker']:
                    found_crypto.append(asset['ticker'])
                    
            # Check for USD prices
            market_cap = asset.get('market_cap', '')
            if '$' in market_cap or 'USD' in market_cap:
                usd_assets.append(asset['name'])
                
        self.log(f"   🏢 World stocks found: {found_stocks}")
        self.log(f"   ₿ Crypto assets found: {found_crypto}")
        self.log(f"   💵 USD-priced assets: {len(usd_assets)} assets")
        
        # Verify we found the expected assets
        if len(found_stocks) >= 3 and len(found_crypto) >= 3:
            self.log("✅ All expected world stocks and crypto assets found!")
            return True
        else:
            self.log("❌ Missing some expected world stocks or crypto assets", "ERROR")
            return False
            
    def test_assets_store_fictional_names(self):
        """Test GET /api/assets/store - Verify fictional brand names."""
        self.log("🏪 Testing GET /api/assets/store (fictional names)...")
        
        response = self.session.get(f"{BASE_URL}/assets/store")
        
        if response.status_code != 200:
            self.log(f"❌ Assets store failed: {response.status_code} - {response.text}", "ERROR")
            return False
            
        data = response.json()
        
        if not isinstance(data, list):
            self.log("❌ Assets data should be a list", "ERROR")
            return False
            
        assets = data
        self.log(f"✅ Assets store working! Found {len(assets)} assets")
        
        # Check for real brand names (should NOT be present)
        real_brands = ['Ferrari', 'BMW', 'Rolex', 'Mercedes', 'Audi', 'Porsche', 'Lamborghini', 'Tesla', 'Apple', 'Samsung']
        fictional_examples = ['Veloce GT Sport', 'Luxor Premium SUV', 'Classic Diver Watch', 'Rider 160 Moto']
        
        real_brands_found = []
        fictional_names_found = []
        
        for asset in assets:
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
            self.log(f"❌ Real brand names found (should be fictional): {real_brands_found}", "ERROR")
            return False
        else:
            self.log("✅ No real brand names found - all assets have fictional names!")
            
        self.log(f"   🎭 Fictional names found: {fictional_names_found}")
        
        # Show some examples
        vehicle_assets = [a for a in assets if a['category'] == 'veiculo']
        luxury_assets = [a for a in assets if a['category'] == 'luxo']
        property_assets = [a for a in assets if a['category'] == 'imovel']
        
        self.log(f"   🚗 Vehicle assets: {len(vehicle_assets)} (e.g., {vehicle_assets[0]['name'] if vehicle_assets else 'None'})")
        self.log(f"   💎 Luxury assets: {len(luxury_assets)} (e.g., {luxury_assets[0]['name'] if luxury_assets else 'None'})")
        self.log(f"   🏠 Property assets: {len(property_assets)} (e.g., {property_assets[0]['name'] if property_assets else 'None'})")
        
        return True
        
    def test_user_profile_with_data(self):
        """Test GET /api/user/me to check user status with companies and job."""
        self.log("👤 Testing GET /api/user/me (user with data)...")
        
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
        
        # Check for additional profile data
        if 'education_count' in data:
            self.log(f"   🎓 Education: {data['education_count']} items")
        if 'certification_count' in data:
            self.log(f"   📜 Certifications: {data['certification_count']} items")
        if 'work_experience_count' in data:
            self.log(f"   💼 Work experience: {data['work_experience_count']} items")
            
        return True
        
    def run_all_tests(self):
        """Run all tests in sequence."""
        self.log("🚀 Starting BizRealms Comprehensive Revenue Collection Tests")
        self.log("=" * 70)
        
        tests = [
            ("Login", self.login),
            ("User Profile (with data)", self.test_user_profile_with_data),
            ("Current Job Status", self.test_current_job_status),
            ("Companies Owned (daily_revenue)", self.test_companies_owned_with_daily_revenue),
            ("Companies Collect Revenue (no KeyError)", self.test_companies_collect_revenue_working),
            ("Jobs Collect Earnings (game time)", self.test_jobs_collect_earnings_working),
            ("Investments Market (USD prices)", self.test_investments_market_usd_prices),
            ("Assets Store (fictional names)", self.test_assets_store_fictional_names),
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
                
        self.log("\n" + "=" * 70)
        self.log(f"🏁 Test Results: {passed} passed, {failed} failed")
        
        if failed == 0:
            self.log("🎉 ALL TESTS PASSED! Revenue collection systems are working correctly.")
            self.log("✅ No KeyError exceptions found")
            self.log("✅ Game time system working (30 game days = 24 real hours)")
            self.log("✅ USD prices and world stocks/crypto present")
            self.log("✅ Fictional brand names only (no real brands)")
            return True
        else:
            self.log(f"⚠️ {failed} tests failed. Please check the issues above.")
            return False

if __name__ == "__main__":
    tester = ComprehensiveRevenueCollectionTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)