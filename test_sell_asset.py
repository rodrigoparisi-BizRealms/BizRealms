#!/usr/bin/env python3
"""
Test asset selling functionality
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

def test_sell_asset(token):
    """Test selling an asset"""
    headers = {'Authorization': f'Bearer {token}'}
    
    # Get owned assets
    response = requests.get(f"{BASE_URL}/assets/owned", headers=headers, timeout=30)
    if response.status_code != 200:
        print("  ❌ Could not get owned assets")
        return False
    
    data = response.json()
    assets = data['assets']
    
    if len(assets) == 0:
        print("  ⚠️ No assets to sell")
        return True
    
    # Sell the first asset
    asset_to_sell = assets[0]
    sell_data = {"asset_id": asset_to_sell['id']}
    
    print(f"  Trying to sell {asset_to_sell['name']}")
    print(f"  Purchase price: R$ {asset_to_sell['purchase_price']:,.2f}")
    print(f"  Current value: R$ {asset_to_sell['current_value']:,.2f}")
    print(f"  Profit/Loss: R$ {asset_to_sell['profit']:,.2f}")
    
    response = requests.post(f"{BASE_URL}/assets/sell", json=sell_data, headers=headers, timeout=30)
    
    print(f"  Result: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"  ✅ Success: {data['message']}")
        print(f"  Sell value: R$ {data['sell_value']:,.2f}")
        print(f"  Profit: R$ {data['profit']:,.2f}")
        print(f"  New balance: R$ {data['new_balance']:,.2f}")
        return True
    else:
        print(f"  ❌ Error: {response.text}")
        return False

def main():
    print("=" * 50)
    print("ASSET SELLING TEST")
    print("=" * 50)
    
    # Login
    token = test_login()
    if not token:
        print("❌ Login failed")
        return
    
    print("✅ Login successful")
    
    print("\n💰 Testing Asset Selling:")
    test_sell_asset(token)
    
    print("\n" + "=" * 50)
    print("ASSET SELLING TEST COMPLETE")
    print("=" * 50)

if __name__ == "__main__":
    main()