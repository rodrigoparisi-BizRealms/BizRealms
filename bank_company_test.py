#!/usr/bin/env python3
"""
Backend API Testing for Business Empire Game - Bank System & Company Sell
Testing the Bank System and Company Sell endpoints as requested in the review
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "https://career-mogul-1.preview.emergentagent.com/api"
TEST_EMAIL = "teste@businessempire.com"
TEST_PASSWORD = "teste123"

class BankCompanyAPITester:
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
    
    def test_bank_account_overview(self):
        """Test GET /api/bank/account - Bank overview with auto-created credit card"""
        print("\n" + "="*60)
        print("🏦 TESTING BANK ACCOUNT OVERVIEW")
        print("="*60)
        
        print("\n📊 Testing GET /api/bank/account...")
        response = requests.get(
            f"{self.base_url}/bank/account",
            headers=self.get_headers()
        )
        
        if response.status_code == 200:
            account = response.json()
            print(f"✅ Bank account overview retrieved successfully!")
            print(f"   Balance: R$ {account.get('balance', 0):,.2f}")
            print(f"   Level: {account.get('level', 1)}")
            
            # Check credit card (should auto-create)
            credit_card = account.get('credit_card', {})
            if credit_card:
                print(f"   Credit Card: {credit_card.get('card_number', 'Unknown')}")
                print(f"   Credit Limit: R$ {credit_card.get('limit', 0):,.2f}")
                print(f"   Balance Used: R$ {credit_card.get('balance_used', 0):,.2f}")
                print(f"   Miles Points: {credit_card.get('miles_points', 0):,}")
                self.credit_card_id = credit_card.get('id')
            else:
                print("⚠️  Credit card not found or not auto-created")
            
            # Check loans
            loans = account.get('loans', [])
            print(f"   Active Loans: {len(loans)}")
            if loans:
                for loan in loans[:2]:  # Show first 2
                    print(f"     • {loan.get('type', 'unknown')} loan: R$ {loan.get('remaining_balance', 0):,.2f}")
            
            # Check available trips
            trips = account.get('available_trips', [])
            print(f"   Available Trips: {len(trips)}")
            if trips:
                for trip in trips[:2]:  # Show first 2
                    print(f"     • {trip.get('name', 'Unknown')}: {trip.get('miles_cost', 0):,} miles")
            
            # Check loan limits
            limits = account.get('loan_limits', {})
            print(f"   Small Loan Limit: R$ {limits.get('small_no_guarantee', 0):,.2f}")
            print(f"   Large Loan Limit: R$ {limits.get('large_with_guarantee', 0):,.2f}")
            
            # Verify required fields
            required_fields = ['balance', 'level', 'credit_card', 'loans', 'available_trips', 'loan_limits']
            missing_fields = [field for field in required_fields if field not in account]
            if missing_fields:
                print(f"⚠️  Missing required fields: {missing_fields}")
            else:
                print("✅ All required fields present in bank account overview!")
                
            return account
        else:
            print(f"❌ Bank account overview failed: {response.status_code} - {response.text}")
            return None
    
    def test_credit_card_purchase(self):
        """Test POST /api/bank/credit-card/purchase - Make purchase and earn miles"""
        print("\n" + "="*60)
        print("💳 TESTING CREDIT CARD PURCHASE")
        print("="*60)
        
        print("\n🛒 Testing POST /api/bank/credit-card/purchase...")
        purchase_data = {
            "amount": 5000,
            "description": "Test purchase for API testing"
        }
        
        response = requests.post(
            f"{self.base_url}/bank/credit-card/purchase",
            json=purchase_data,
            headers=self.get_headers()
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Credit card purchase successful!")
            print(f"   Message: {result.get('message', '')}")
            print(f"   Miles Earned: {result.get('miles_earned', 0):,}")
            print(f"   Total Miles: {result.get('total_miles', 0):,}")
            print(f"   Balance Used: R$ {result.get('balance_used', 0):,.2f}")
            
            # Verify miles calculation (1 mile per R$1)
            expected_miles = int(purchase_data['amount'])
            actual_miles = result.get('miles_earned', 0)
            if actual_miles == expected_miles:
                print("✅ Miles calculation correct (1 mile per R$1)!")
            else:
                print(f"⚠️  Miles calculation incorrect. Expected: {expected_miles}, Got: {actual_miles}")
                
            return result
        else:
            print(f"❌ Credit card purchase failed: {response.status_code} - {response.text}")
            return None
    
    def test_credit_card_pay_bill(self):
        """Test POST /api/bank/credit-card/pay-bill - Pay credit card bill"""
        print("\n" + "="*60)
        print("💰 TESTING CREDIT CARD BILL PAYMENT")
        print("="*60)
        
        print("\n💳 Testing POST /api/bank/credit-card/pay-bill...")
        # Pay full bill (amount = 0 means pay full)
        payment_data = {
            "amount": 0  # 0 = pay full bill as mentioned in review request
        }
        
        response = requests.post(
            f"{self.base_url}/bank/credit-card/pay-bill",
            json=payment_data,
            headers=self.get_headers()
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Credit card bill payment successful!")
            print(f"   Message: {result.get('message', '')}")
            print(f"   New Balance: R$ {result.get('new_balance', 0):,.2f}")
            print(f"   Remaining Bill: R$ {result.get('remaining_bill', 0):,.2f}")
            
            # Verify bill is cleared
            remaining = result.get('remaining_bill', 0)
            if remaining == 0:
                print("✅ Credit card bill fully cleared!")
            else:
                print(f"⚠️  Bill not fully cleared. Remaining: R$ {remaining:,.2f}")
                
            return result
        else:
            print(f"❌ Credit card bill payment failed: {response.status_code} - {response.text}")
            return None
    
    def test_redeem_miles(self):
        """Test POST /api/bank/credit-card/redeem-miles - Redeem miles for trip"""
        print("\n" + "="*60)
        print("✈️  TESTING MILES REDEMPTION")
        print("="*60)
        
        print("\n🎫 Testing POST /api/bank/credit-card/redeem-miles...")
        # Try to redeem trip_nacional (5000 miles as mentioned in review request)
        redemption_data = {
            "trip_id": "trip_nacional"
        }
        
        response = requests.post(
            f"{self.base_url}/bank/credit-card/redeem-miles",
            json=redemption_data,
            headers=self.get_headers()
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Miles redemption successful!")
            print(f"   Message: {result.get('message', '')}")
            print(f"   Trip Name: {result.get('trip_name', '')}")
            print(f"   XP Gained: {result.get('xp_gained', 0):,}")
            print(f"   Miles Spent: {result.get('miles_spent', 0):,}")
            print(f"   Remaining Miles: {result.get('remaining_miles', 0):,}")
            
            # Verify XP reward
            expected_xp = 2000  # trip_nacional should give 2000 XP
            actual_xp = result.get('xp_gained', 0)
            if actual_xp == expected_xp:
                print("✅ XP reward correct for trip_nacional!")
            else:
                print(f"⚠️  XP reward incorrect. Expected: {expected_xp}, Got: {actual_xp}")
                
            return result
        elif response.status_code == 400:
            error_detail = response.json().get('detail', 'Unknown error')
            if "insuficientes" in error_detail:
                print(f"⚠️  Insufficient miles for redemption: {error_detail}")
                print("   This is expected if user doesn't have 5000 miles yet")
            else:
                print(f"⚠️  Miles redemption failed: {error_detail}")
            return None
        else:
            print(f"❌ Miles redemption failed: {response.status_code} - {response.text}")
            return None
    
    def test_loan_apply(self):
        """Test POST /api/bank/loan/apply - Apply for small loan"""
        print("\n" + "="*60)
        print("🏦 TESTING LOAN APPLICATION")
        print("="*60)
        
        print("\n📋 Testing POST /api/bank/loan/apply (small loan)...")
        loan_data = {
            "amount": 10000,
            "type": "small",
            "months": 12
        }
        
        response = requests.post(
            f"{self.base_url}/bank/loan/apply",
            json=loan_data,
            headers=self.get_headers()
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Loan application successful!")
            print(f"   Message: {result.get('message', '')}")
            print(f"   Loan ID: {result.get('loan_id', '')}")
            print(f"   Monthly Payment: R$ {result.get('monthly_payment', 0):,.2f}")
            print(f"   Total with Interest: R$ {result.get('total_with_interest', 0):,.2f}")
            print(f"   Months: {result.get('months', 0)}")
            print(f"   New Balance: R$ {result.get('new_balance', 0):,.2f}")
            
            # Store loan ID for payment tests
            self.loan_id = result.get('loan_id')
            
            # Verify money was added to user balance
            new_balance = result.get('new_balance', 0)
            if new_balance > 0:
                print("✅ Money successfully added to user balance!")
            else:
                print("⚠️  Money not added to user balance")
                
            return result
        elif response.status_code == 400:
            error_detail = response.json().get('detail', 'Unknown error')
            if "Limite de 3 empréstimos" in error_detail:
                print(f"⚠️  Loan limit reached: {error_detail}")
                print("   This is expected if user already has 3 active loans")
            else:
                print(f"⚠️  Loan application failed: {error_detail}")
            return None
        else:
            print(f"❌ Loan application failed: {response.status_code} - {response.text}")
            return None
    
    def test_loan_pay_installment(self):
        """Test POST /api/bank/loan/pay - Pay monthly loan installment"""
        print("\n" + "="*60)
        print("💳 TESTING LOAN INSTALLMENT PAYMENT")
        print("="*60)
        
        if not hasattr(self, 'loan_id') or not self.loan_id:
            print("⚠️  No loan ID available. Skipping installment payment test.")
            return None
        
        print("\n💰 Testing POST /api/bank/loan/pay...")
        payment_data = {
            "loan_id": self.loan_id
        }
        
        response = requests.post(
            f"{self.base_url}/bank/loan/pay",
            json=payment_data,
            headers=self.get_headers()
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Loan installment payment successful!")
            print(f"   Message: {result.get('message', '')}")
            print(f"   Payment Number: {result.get('payment_number', 0)}")
            print(f"   Remaining Balance: R$ {result.get('remaining_balance', 0):,.2f}")
            print(f"   Status: {result.get('status', '')}")
            print(f"   New Balance: R$ {result.get('new_balance', 0):,.2f}")
            
            # Verify payment was processed
            payment_num = result.get('payment_number', 0)
            if payment_num > 0:
                print("✅ Loan payment successfully processed!")
            else:
                print("⚠️  Loan payment not processed correctly")
                
            return result
        elif response.status_code == 400:
            error_detail = response.json().get('detail', 'Unknown error')
            if "insuficiente" in error_detail:
                print(f"⚠️  Insufficient funds for loan payment: {error_detail}")
            else:
                print(f"⚠️  Loan payment failed: {error_detail}")
            return None
        else:
            print(f"❌ Loan installment payment failed: {response.status_code} - {response.text}")
            return None
    
    def test_loan_payoff(self):
        """Test POST /api/bank/loan/payoff - Pay off entire loan with discount"""
        print("\n" + "="*60)
        print("💰 TESTING LOAN PAYOFF")
        print("="*60)
        
        if not hasattr(self, 'loan_id') or not self.loan_id:
            print("⚠️  No loan ID available. Skipping payoff test.")
            return None
        
        print("\n🏦 Testing POST /api/bank/loan/payoff...")
        payoff_data = {
            "loan_id": self.loan_id
        }
        
        response = requests.post(
            f"{self.base_url}/bank/loan/payoff",
            json=payoff_data,
            headers=self.get_headers()
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Loan payoff successful!")
            print(f"   Message: {result.get('message', '')}")
            print(f"   Payoff Amount: R$ {result.get('payoff_amount', 0):,.2f}")
            print(f"   Savings: R$ {result.get('savings', 0):,.2f}")
            print(f"   New Balance: R$ {result.get('new_balance', 0):,.2f}")
            
            # Verify savings (should be positive for early payoff discount)
            savings = result.get('savings', 0)
            if savings > 0:
                print("✅ Early payoff discount applied successfully!")
            else:
                print("⚠️  No savings from early payoff (may be expected if loan was almost paid)")
                
            return result
        elif response.status_code == 400:
            error_detail = response.json().get('detail', 'Unknown error')
            if "insuficiente" in error_detail:
                print(f"⚠️  Insufficient funds for loan payoff: {error_detail}")
            else:
                print(f"⚠️  Loan payoff failed: {error_detail}")
            return None
        elif response.status_code == 404:
            print("⚠️  Loan not found (may have been paid off already)")
            return None
        else:
            print(f"❌ Loan payoff failed: {response.status_code} - {response.text}")
            return None
    
    def test_company_sell(self):
        """Test POST /api/companies/sell - Sell owned company"""
        print("\n" + "="*60)
        print("🏢 TESTING COMPANY SELL SYSTEM")
        print("="*60)
        
        # First, get owned companies
        print("\n🔍 Getting owned companies...")
        response = requests.get(
            f"{self.base_url}/companies/owned",
            headers=self.get_headers()
        )
        
        company_to_sell = None
        if response.status_code == 200:
            companies_data = response.json()
            companies = companies_data.get('companies', [])
            print(f"   User owns {len(companies)} companies")
            
            if companies:
                # Find a company to sell (prefer non-franchise)
                for company in companies:
                    if not company.get('is_franchise', False):
                        company_to_sell = company
                        break
                
                if not company_to_sell and companies:
                    company_to_sell = companies[0]  # Use any company if no non-franchise found
                
                if company_to_sell:
                    print(f"   Selected company to sell: {company_to_sell.get('name', 'Unknown')}")
                    print(f"   Purchase Price: R$ {company_to_sell.get('purchase_price', 0):,.2f}")
                    print(f"   Is Franchise: {company_to_sell.get('is_franchise', False)}")
            else:
                print("   User has no companies to sell")
        else:
            print(f"❌ Failed to get owned companies: {response.status_code} - {response.text}")
        
        if not company_to_sell:
            print("⚠️  No companies available to sell. Skipping company sell test.")
            return None
        
        # Test company sell
        print(f"\n🏪 Testing POST /api/companies/sell...")
        sell_data = {
            "company_id": company_to_sell['id']
        }
        
        response = requests.post(
            f"{self.base_url}/companies/sell",
            json=sell_data,
            headers=self.get_headers()
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Company sell successful!")
            print(f"   Message: {result.get('message', '')}")
            print(f"   Sell Price: R$ {result.get('sell_price', 0):,.2f}")
            print(f"   New Balance: R$ {result.get('new_balance', 0):,.2f}")
            
            # Verify sell price (should be 80% of purchase price)
            purchase_price = company_to_sell.get('purchase_price', 0)
            expected_sell_price = round(purchase_price * 0.8)
            actual_sell_price = result.get('sell_price', 0)
            
            if actual_sell_price == expected_sell_price:
                print("✅ Sell price calculation correct (80% of purchase price)!")
            else:
                print(f"⚠️  Sell price calculation incorrect. Expected: R$ {expected_sell_price:,.2f}, Got: R$ {actual_sell_price:,.2f}")
            
            # Check if franchises were deleted (if it was a parent company)
            if not company_to_sell.get('is_franchise', False):
                print("✅ Parent company sold - franchises should be automatically deleted")
            
            return result
        elif response.status_code == 404:
            print(f"❌ Company not found: {response.json().get('detail', 'Unknown error')}")
            return None
        else:
            print(f"❌ Company sell failed: {response.status_code} - {response.text}")
            return None
    
    def run_all_tests(self):
        """Run all Bank System and Company Sell tests"""
        print("🚀 STARTING BANK SYSTEM & COMPANY SELL TESTING")
        print("="*80)
        print(f"Backend URL: {self.base_url}")
        print(f"Test User: {TEST_EMAIL}")
        print("="*80)
        
        # Login first
        if not self.login():
            print("❌ Cannot proceed without login!")
            return
        
        # Run all tests in sequence
        try:
            # Bank System Tests
            account_data = self.test_bank_account_overview()
            
            if account_data:
                self.test_credit_card_purchase()
                
                # Get account again to verify miles increased
                print("\n🔄 Checking account after purchase to verify miles...")
                updated_account = self.test_bank_account_overview()
                
                self.test_credit_card_pay_bill()
                self.test_redeem_miles()
                
                loan_result = self.test_loan_apply()
                if loan_result:
                    self.test_loan_pay_installment()
                    self.test_loan_payoff()
            
            # Company Sell Test
            self.test_company_sell()
            
            print("\n" + "="*80)
            print("🎉 ALL BANK SYSTEM & COMPANY SELL TESTS COMPLETED!")
            print("="*80)
            
        except Exception as e:
            print(f"\n❌ Test execution failed with error: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    tester = BankCompanyAPITester()
    tester.run_all_tests()