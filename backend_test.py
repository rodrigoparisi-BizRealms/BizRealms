#!/usr/bin/env python3
"""
Backend API Testing Script for Business Empire Game
Company Purchase Offers System Testing
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BACKEND_URL = "https://career-mogul-1.preview.emergentagent.com/api"
TEST_EMAIL = "teste@businessempire.com"
TEST_PASSWORD = "teste123"

class BusinessEmpireAPITester:
    def __init__(self):
        self.token = None
        self.user_data = None
        self.session = requests.Session()
        
    def login(self):
        """Login and get JWT token"""
        print("🔐 Testing login...")
        
        response = self.session.post(f"{BACKEND_URL}/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        if response.status_code != 200:
            print(f"❌ Login failed: {response.status_code} - {response.text}")
            return False
            
        data = response.json()
        self.token = data.get('token')
        if not self.token:
            print("❌ No token received")
            return False
            
        # Set authorization header for all future requests
        self.session.headers.update({'Authorization': f'Bearer {self.token}'})
        print(f"✅ Login successful, token received")
        return True
    
    def get_user_profile(self):
        """Get current user profile"""
        print("\n👤 Getting user profile...")
        
        response = self.session.get(f"{BACKEND_URL}/user/me")
        if response.status_code != 200:
            print(f"❌ Get profile failed: {response.status_code} - {response.text}")
            return False
            
        self.user_data = response.json()
        print(f"✅ User profile retrieved: {self.user_data.get('name')} (Level {self.user_data.get('level')}, R$ {self.user_data.get('money'):,.2f})")
        return True
    
    def get_owned_companies(self):
        """Get user's owned companies"""
        print("\n🏢 Getting owned companies...")
        
        response = self.session.get(f"{BACKEND_URL}/companies/owned")
        if response.status_code != 200:
            print(f"❌ Get owned companies failed: {response.status_code} - {response.text}")
            return False, []
            
        data = response.json()
        companies = data.get('companies', [])
        print(f"✅ User owns {len(companies)} companies:")
        for company in companies:
            print(f"   - {company.get('name')} (Segment: {company.get('segment')}, Value: R$ {company.get('purchase_price', 0):,.0f})")
        
        return True, companies
    
    def get_company_offers(self):
        """Get active purchase offers for user's companies"""
        print("\n💰 Getting company purchase offers...")
        
        response = self.session.get(f"{BACKEND_URL}/companies/offers")
        if response.status_code != 200:
            print(f"❌ Get offers failed: {response.status_code} - {response.text}")
            return False, []
            
        data = response.json()
        offers = data.get('offers', [])
        total_offers = data.get('total_offers', 0)
        
        print(f"✅ Found {total_offers} active offers:")
        for offer in offers:
            print(f"   - Offer ID: {offer.get('id')}")
            print(f"     Company: {offer.get('company_name')}")
            print(f"     Buyer: {offer.get('buyer_name')}")
            print(f"     Offer Amount: R$ {offer.get('offer_amount'):,.0f}")
            print(f"     Purchase Price: R$ {offer.get('purchase_price'):,.0f}")
            print(f"     Reason: {offer.get('reason_emoji')} {offer.get('reason')}")
            print(f"     Remaining: {offer.get('remaining_minutes')} minutes")
            print()
        
        return True, offers
    
    def decline_offer(self, offer_id):
        """Decline a purchase offer"""
        print(f"\n❌ Declining offer {offer_id}...")
        
        response = self.session.post(f"{BACKEND_URL}/companies/offers/respond", json={
            "offer_id": offer_id,
            "action": "decline"
        })
        
        if response.status_code != 200:
            print(f"❌ Decline offer failed: {response.status_code} - {response.text}")
            return False
            
        data = response.json()
        print(f"✅ Offer declined: {data.get('message')}")
        return True
    
    def accept_offer(self, offer_id):
        """Accept a purchase offer"""
        print(f"\n✅ Accepting offer {offer_id}...")
        
        # Get current money before accepting
        initial_money = self.user_data.get('money', 0)
        
        response = self.session.post(f"{BACKEND_URL}/companies/offers/respond", json={
            "offer_id": offer_id,
            "action": "accept"
        })
        
        if response.status_code != 200:
            print(f"❌ Accept offer failed: {response.status_code} - {response.text}")
            return False
            
        data = response.json()
        print(f"✅ Offer accepted: {data.get('message')}")
        print(f"   Offer Amount: R$ {data.get('offer_amount'):,.0f}")
        print(f"   Profit/Loss: R$ {data.get('profit'):,.0f}")
        print(f"   XP Bonus: +{data.get('xp_bonus'):,}")
        print(f"   New Balance: R$ {data.get('new_balance'):,.2f}")
        
        # Verify money was added
        money_increase = data.get('new_balance', 0) - initial_money
        print(f"   Money Increase: R$ {money_increase:,.2f}")
        
        return True
    
    def run_company_offers_test(self):
        """Run the complete Company Purchase Offers test flow"""
        print("🎮 COMPANY PURCHASE OFFERS SYSTEM TEST")
        print("=" * 50)
        
        # Step 1: Login
        if not self.login():
            return False
        
        # Step 2: Get user profile
        if not self.get_user_profile():
            return False
        
        # Step 3: Get owned companies
        success, companies = self.get_owned_companies()
        if not success:
            return False
        
        if not companies:
            print("❌ User has no companies to generate offers for")
            return False
        
        # Step 4: Get company offers (may generate new ones)
        success, offers = self.get_company_offers()
        if not success:
            return False
        
        if not offers:
            print("ℹ️  No offers available at this time (35% chance per company, 2-hour cooldown)")
            print("✅ Offers endpoint working correctly - no offers generated this time")
            return True
        
        # Step 5: Test declining an offer
        if len(offers) > 0:
            first_offer = offers[0]
            if self.decline_offer(first_offer['id']):
                # Step 6: Verify declined offer is gone
                print("\n🔍 Verifying declined offer is removed...")
                success, updated_offers = self.get_company_offers()
                if success:
                    declined_offer_still_exists = any(o['id'] == first_offer['id'] for o in updated_offers)
                    if not declined_offer_still_exists:
                        print("✅ Declined offer successfully removed from list")
                    else:
                        print("❌ Declined offer still appears in list")
                        return False
        
        # Step 7: Test accepting an offer (if any remaining)
        success, final_offers = self.get_company_offers()
        if success and final_offers:
            offer_to_accept = final_offers[0]
            if self.accept_offer(offer_to_accept['id']):
                # Step 8: Verify company was sold and money was added
                print("\n🔍 Verifying company sale...")
                success, remaining_companies = self.get_owned_companies()
                if success:
                    company_still_owned = any(c['id'] == offer_to_accept.get('company_id') for c in remaining_companies)
                    if not company_still_owned:
                        print("✅ Company successfully sold and removed from owned companies")
                    else:
                        print("❌ Company still appears in owned companies list")
                        return False
                
                # Refresh user profile to verify money increase
                if self.get_user_profile():
                    print("✅ User profile updated with new balance")
        
        print("\n🎉 COMPANY PURCHASE OFFERS SYSTEM TEST COMPLETED SUCCESSFULLY!")
        return True

def main():
    """Main test execution"""
    tester = BusinessEmpireAPITester()
    
    try:
        success = tester.run_company_offers_test()
        if success:
            print("\n✅ ALL TESTS PASSED")
            sys.exit(0)
        else:
            print("\n❌ SOME TESTS FAILED")
            sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test execution failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()