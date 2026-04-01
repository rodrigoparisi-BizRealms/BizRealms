#!/usr/bin/env python3
"""
Test Companies and Assets buy/sell operations
"""

import requests
import json

BASE_URL = "https://career-mogul-1.preview.emergentagent.com/api"
TEST_USER = {
    "email": "test_jobs@businessempire.com",
    "password": "test123"
}

def test_login():
    """Login and get token"""
    response = requests.post(f"{BASE_URL}/auth/login", json=TEST_USER, timeout=30)
    if response.status_code == 200:
        data = response.json()
        return data['token']
    return None

def test_user_money(token):
    """Check user money"""
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(f"{BASE_URL}/user/stats", headers=headers, timeout=30)
    if response.status_code == 200:
        data = response.json()
        return data.get('money', 0)
    return 0

def test_buy_company(token):
    """Test buying a company"""
    headers = {'Authorization': f'Bearer {token}'}
    
    # Get available companies
    response = requests.get(f"{BASE_URL}/companies/available", headers=headers, timeout=30)
    if response.status_code != 200:
        return False
    
    companies = response.json()
    # Find cheapest company not already owned
    available = [c for c in companies if not c.get('already_owned', False)]
    if not available:
        print("  No companies available to buy")
        return True
    
    cheapest = min(available, key=lambda c: c.get('price', float('inf')))
    
    # Try to buy it
    buy_data = {"company_id": cheapest['id']}
    response = requests.post(f"{BASE_URL}/companies/buy", json=buy_data, headers=headers, timeout=30)
    
    print(f"  Trying to buy {cheapest['name']} for R$ {cheapest['price']:,.2f}")
    print(f"  Result: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"  ✅ Success: {data['message']}")
        return True
    elif response.status_code == 400:
        print(f"  ⚠️ Expected failure: {response.json().get('detail', 'Unknown error')}")
        return True
    else:
        print(f"  ❌ Unexpected error: {response.text}")
        return False

def test_create_company(token):
    """Test creating a custom company"""
    headers = {'Authorization': f'Bearer {token}'}
    
    create_data = {
        "name": "Test Automation Corp",
        "segment": "tecnologia"
    }
    
    response = requests.post(f"{BASE_URL}/companies/create", json=create_data, headers=headers, timeout=30)
    
    print(f"  Trying to create {create_data['name']} in {create_data['segment']} segment")
    print(f"  Result: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"  ✅ Success: {data['message']}")
        return True
    elif response.status_code == 400:
        print(f"  ⚠️ Expected failure: {response.json().get('detail', 'Unknown error')}")
        return True
    else:
        print(f"  ❌ Unexpected error: {response.text}")
        return False

def test_buy_asset(token):
    """Test buying an asset"""
    headers = {'Authorization': f'Bearer {token}'}
    
    # Get available assets
    response = requests.get(f"{BASE_URL}/assets/store", headers=headers, timeout=30)
    if response.status_code != 200:
        return False
    
    assets = response.json()
    # Find cheapest asset not already owned
    available = [a for a in assets if not a.get('already_owned', False)]
    if not available:
        print("  No assets available to buy")
        return True
    
    cheapest = min(available, key=lambda a: a.get('price', float('inf')))
    
    # Try to buy it
    buy_data = {"asset_id": cheapest['id']}
    response = requests.post(f"{BASE_URL}/assets/buy", json=buy_data, headers=headers, timeout=30)
    
    print(f"  Trying to buy {cheapest['name']} for R$ {cheapest['price']:,.2f}")
    print(f"  Result: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"  ✅ Success: {data['message']}")
        return True
    elif response.status_code == 400:
        print(f"  ⚠️ Expected failure: {response.json().get('detail', 'Unknown error')}")
        return True
    else:
        print(f"  ❌ Unexpected error: {response.text}")
        return False

def test_merge_companies(token):
    """Test merging companies"""
    headers = {'Authorization': f'Bearer {token}'}
    
    # Get owned companies
    response = requests.get(f"{BASE_URL}/companies/owned", headers=headers, timeout=30)
    if response.status_code != 200:
        return False
    
    data = response.json()
    companies = data['companies']
    
    if len(companies) < 2:
        print("  Need at least 2 companies to test merge")
        return True
    
    # Find two companies of same segment
    segments = {}
    for company in companies:
        segment = company.get('segment')
        if segment not in segments:
            segments[segment] = []
        segments[segment].append(company)
    
    merge_candidates = None
    for segment, companies_in_segment in segments.items():
        if len(companies_in_segment) >= 2:
            merge_candidates = companies_in_segment[:2]
            break
    
    if not merge_candidates:
        print("  No two companies of same segment to merge")
        return True
    
    merge_data = {
        "company_id_1": merge_candidates[0]['id'],
        "company_id_2": merge_candidates[1]['id']
    }
    
    response = requests.post(f"{BASE_URL}/companies/merge", json=merge_data, headers=headers, timeout=30)
    
    print(f"  Trying to merge {merge_candidates[0]['name']} + {merge_candidates[1]['name']}")
    print(f"  Result: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"  ✅ Success: {data['message']}")
        return True
    else:
        print(f"  ❌ Error: {response.text}")
        return False

def main():
    print("=" * 60)
    print("COMPANIES & ASSETS TRANSACTION TESTING")
    print("=" * 60)
    
    # Login
    token = test_login()
    if not token:
        print("❌ Login failed")
        return
    
    print("✅ Login successful")
    
    # Check user money
    money = test_user_money(token)
    print(f"💰 User has R$ {money:,.2f}")
    
    print("\n🏢 Testing Company Operations:")
    test_buy_company(token)
    test_create_company(token)
    test_merge_companies(token)
    
    print("\n🏠 Testing Asset Operations:")
    test_buy_asset(token)
    
    print("\n" + "=" * 60)
    print("TRANSACTION TESTING COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()