#!/usr/bin/env python3
"""
Quick test for Companies and Assets endpoints
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

def test_companies_endpoints(token):
    """Test all companies endpoints"""
    headers = {'Authorization': f'Bearer {token}'}
    
    print("Testing Companies Endpoints:")
    
    # 1. Get available companies
    response = requests.get(f"{BASE_URL}/companies/available", headers=headers, timeout=30)
    print(f"GET /companies/available: {response.status_code}")
    if response.status_code == 200:
        companies = response.json()
        print(f"  Found {len(companies)} companies for sale")
    
    # 2. Get owned companies
    response = requests.get(f"{BASE_URL}/companies/owned", headers=headers, timeout=30)
    print(f"GET /companies/owned: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"  User owns {data['count']} companies")
    
    # 3. Try to collect revenue
    response = requests.post(f"{BASE_URL}/companies/collect-revenue", headers=headers, timeout=30)
    print(f"POST /companies/collect-revenue: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"  Revenue collected: R$ {data.get('total_revenue', 0):.2f}")
    elif response.status_code == 400:
        print("  No companies owned (expected)")
    
    # 4. Try ad boost
    response = requests.post(f"{BASE_URL}/companies/ad-boost", headers=headers, timeout=30)
    print(f"POST /companies/ad-boost: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"  Boosted {data.get('companies_boosted', 0)} companies")
    elif response.status_code == 400:
        print("  No companies owned (expected)")

def test_assets_endpoints(token):
    """Test all assets endpoints"""
    headers = {'Authorization': f'Bearer {token}'}
    
    print("\nTesting Assets Endpoints:")
    
    # 1. Get assets store
    response = requests.get(f"{BASE_URL}/assets/store", headers=headers, timeout=30)
    print(f"GET /assets/store: {response.status_code}")
    if response.status_code == 200:
        assets = response.json()
        print(f"  Found {len(assets)} assets for sale")
        categories = set(asset.get('category') for asset in assets)
        print(f"  Categories: {categories}")
    
    # 2. Get owned assets
    response = requests.get(f"{BASE_URL}/assets/owned", headers=headers, timeout=30)
    print(f"GET /assets/owned: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"  User owns {data['summary']['count']} assets")
        print(f"  Total value: R$ {data['summary']['total_value']:,.2f}")

def main():
    print("=" * 50)
    print("COMPANIES & ASSETS ENDPOINTS TEST")
    print("=" * 50)
    
    # Login
    token = test_login()
    if not token:
        print("❌ Login failed")
        return
    
    print("✅ Login successful")
    
    # Test endpoints
    test_companies_endpoints(token)
    test_assets_endpoints(token)
    
    print("\n" + "=" * 50)
    print("TEST COMPLETE")
    print("=" * 50)

if __name__ == "__main__":
    main()