#!/usr/bin/env python3
"""
Business Empire Investment System Backend Test Suite
Testing all investment endpoints as requested in the review
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BASE_URL = "https://career-mogul-1.preview.emergentagent.com/api"
TEST_USER = {
    "email": "test_jobs@businessempire.com",
    "password": "test123"
}

# Global variables
auth_token = None
user_data = None
btc_asset_id = None
test_asset_id = None

def log_test(test_name, success, details=""):
    """Log test results"""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status} {test_name}")
    if details:
        print(f"   {details}")
    print()

def make_request(method, endpoint, data=None, headers=None):
    """Make HTTP request with error handling"""
    url = f"{BASE_URL}{endpoint}"
    
    if headers is None:
        headers = {}
    
    if auth_token and 'Authorization' not in headers:
        headers['Authorization'] = f'Bearer {auth_token}'
    
    try:
        if method == 'GET':
            response = requests.get(url, headers=headers, timeout=30)
        elif method == 'POST':
            headers['Content-Type'] = 'application/json'
            response = requests.post(url, json=data, headers=headers, timeout=30)
        elif method == 'PUT':
            headers['Content-Type'] = 'application/json'
            response = requests.put(url, json=data, headers=headers, timeout=30)
        elif method == 'DELETE':
            response = requests.delete(url, headers=headers, timeout=30)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        return response
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        # Create a mock response for connection issues
        class MockResponse:
            def __init__(self):
                self.status_code = 0
                self.text = f"Connection error: {e}"
        return MockResponse()

def test_user_login():
    """Login with existing test user"""
    global auth_token, user_data
    
    login_data = {
        "email": TEST_USER["email"],
        "password": TEST_USER["password"]
    }
    
    response = make_request('POST', '/auth/login', login_data)
    
    if not response or response.status_code != 200:
        log_test("User Login", False, f"Status: {response.status_code if response else 'No response'}")
        return False
    
    try:
        data = response.json()
        auth_token = data['token']
        user_data = data['user']
        log_test("User Login", True, f"User logged in: {user_data['email']}, Money: R$ {user_data.get('money', 0):.2f}")
        return True
    except json.JSONDecodeError:
        log_test("User Login", False, "Invalid JSON response")
        return False

def test_get_market_all():
    """Test 1: GET /api/investments/market - Get all assets"""
    global btc_asset_id, test_asset_id
    
    response = make_request('GET', '/investments/market')
    
    if not response:
        log_test("Get Market (All Assets)", False, "Request failed")
        return False
    
    if response.status_code != 200:
        log_test("Get Market (All Assets)", False, f"Status: {response.status_code}, Response: {response.text}")
        return False
    
    try:
        assets = response.json()
        if not isinstance(assets, list):
            log_test("Get Market (All Assets)", False, "Response is not a list")
            return False
        
        if len(assets) != 22:
            log_test("Get Market (All Assets)", False, f"Expected 22 assets, got {len(assets)}")
            return False
        
        # Find BTC asset for later tests
        for asset in assets:
            if asset.get('ticker') == 'BTC':
                btc_asset_id = asset['id']
            if not test_asset_id:  # Use first asset as test asset
                test_asset_id = asset['id']
        
        # Verify required fields
        required_fields = ['id', 'ticker', 'name', 'category', 'current_price', 'daily_change', 'daily_change_pct', 'sparkline']
        for asset in assets[:3]:  # Check first 3 assets
            for field in required_fields:
                if field not in asset:
                    log_test("Get Market (All Assets)", False, f"Missing field '{field}' in asset {asset.get('ticker', 'unknown')}")
                    return False
        
        # Check sparkline data
        if not assets[0]['sparkline'] or len(assets[0]['sparkline']) != 7:
            log_test("Get Market (All Assets)", False, "Sparkline data missing or incorrect length")
            return False
        
        log_test("Get Market (All Assets)", True, f"Retrieved {len(assets)} assets with tickers, prices, daily changes, and sparklines")
        return True
        
    except json.JSONDecodeError:
        log_test("Get Market (All Assets)", False, "Invalid JSON response")
        return False

def test_get_market_crypto():
    """Test 2: GET /api/investments/market?category=crypto - Filter by crypto"""
    response = make_request('GET', '/investments/market?category=crypto')
    
    if not response:
        log_test("Get Market (Crypto Filter)", False, "Request failed")
        return False
    
    if response.status_code != 200:
        log_test("Get Market (Crypto Filter)", False, f"Status: {response.status_code}, Response: {response.text}")
        return False
    
    try:
        assets = response.json()
        if not isinstance(assets, list):
            log_test("Get Market (Crypto Filter)", False, "Response is not a list")
            return False
        
        # Should only return crypto assets
        for asset in assets:
            if asset.get('category') != 'crypto':
                log_test("Get Market (Crypto Filter)", False, f"Non-crypto asset found: {asset.get('ticker')} ({asset.get('category')})")
                return False
        
        # Should have 5 crypto assets based on the seeds
        if len(assets) != 5:
            log_test("Get Market (Crypto Filter)", False, f"Expected 5 crypto assets, got {len(assets)}")
            return False
        
        log_test("Get Market (Crypto Filter)", True, f"Retrieved {len(assets)} crypto assets only")
        return True
        
    except json.JSONDecodeError:
        log_test("Get Market (Crypto Filter)", False, "Invalid JSON response")
        return False

def test_get_market_acoes():
    """Test 3: GET /api/investments/market?category=acoes - Filter by B3 stocks"""
    response = make_request('GET', '/investments/market?category=acoes')
    
    if not response:
        log_test("Get Market (B3 Stocks Filter)", False, "Request failed")
        return False
    
    if response.status_code != 200:
        log_test("Get Market (B3 Stocks Filter)", False, f"Status: {response.status_code}, Response: {response.text}")
        return False
    
    try:
        assets = response.json()
        if not isinstance(assets, list):
            log_test("Get Market (B3 Stocks Filter)", False, "Response is not a list")
            return False
        
        # Should only return B3 stock assets
        for asset in assets:
            if asset.get('category') != 'acoes':
                log_test("Get Market (B3 Stocks Filter)", False, f"Non-stock asset found: {asset.get('ticker')} ({asset.get('category')})")
                return False
        
        # Should have 8 B3 stocks based on the seeds
        if len(assets) != 8:
            log_test("Get Market (B3 Stocks Filter)", False, f"Expected 8 B3 stock assets, got {len(assets)}")
            return False
        
        log_test("Get Market (B3 Stocks Filter)", True, f"Retrieved {len(assets)} B3 stock assets only")
        return True
        
    except json.JSONDecodeError:
        log_test("Get Market (B3 Stocks Filter)", False, "Invalid JSON response")
        return False

def test_get_asset_history():
    """Test 4: GET /api/investments/asset/{asset_id}/history?days=30 - Get price history"""
    if not test_asset_id:
        log_test("Get Asset History", False, "No asset ID available from previous test")
        return False
    
    response = make_request('GET', f'/investments/asset/{test_asset_id}/history?days=30')
    
    if not response:
        log_test("Get Asset History", False, "Request failed")
        return False
    
    if response.status_code != 200:
        log_test("Get Asset History", False, f"Status: {response.status_code}, Response: {response.text}")
        return False
    
    try:
        data = response.json()
        
        required_fields = ['asset', 'history', 'current_price']
        for field in required_fields:
            if field not in data:
                log_test("Get Asset History", False, f"Missing field: {field}")
                return False
        
        history = data['history']
        if not isinstance(history, list):
            log_test("Get Asset History", False, "History is not a list")
            return False
        
        if len(history) != 30:
            log_test("Get Asset History", False, f"Expected 30 days of history, got {len(history)}")
            return False
        
        # Check history entry format
        for entry in history[:3]:  # Check first 3 entries
            required_entry_fields = ['date', 'price', 'volume']
            for field in required_entry_fields:
                if field not in entry:
                    log_test("Get Asset History", False, f"Missing field '{field}' in history entry")
                    return False
        
        log_test("Get Asset History", True, f"Retrieved 30-day price history for asset {data['asset']['ticker']}")
        return True
        
    except json.JSONDecodeError:
        log_test("Get Asset History", False, "Invalid JSON response")
        return False

def test_buy_asset_first():
    """Test 5: POST /api/investments/buy - Buy BTC (first purchase)"""
    if not btc_asset_id:
        log_test("Buy Asset (First)", False, "No BTC asset ID available")
        return False
    
    buy_data = {
        "asset_id": btc_asset_id,
        "quantity": 0.01
    }
    
    response = make_request('POST', '/investments/buy', buy_data)
    
    if not response:
        log_test("Buy Asset (First)", False, "Request failed")
        return False
    
    if response.status_code != 200:
        log_test("Buy Asset (First)", False, f"Status: {response.status_code}, Response: {response.text}")
        return False
    
    try:
        data = response.json()
        
        required_fields = ['message', 'ticker', 'quantity', 'price', 'total_cost', 'new_balance']
        for field in required_fields:
            if field not in data:
                log_test("Buy Asset (First)", False, f"Missing field: {field}")
                return False
        
        if data['ticker'] != 'BTC':
            log_test("Buy Asset (First)", False, f"Expected BTC ticker, got {data['ticker']}")
            return False
        
        if data['quantity'] != 0.01:
            log_test("Buy Asset (First)", False, f"Expected quantity 0.01, got {data['quantity']}")
            return False
        
        log_test("Buy Asset (First)", True, f"Bought {data['quantity']} {data['ticker']} for R$ {data['total_cost']:.2f}")
        return True
        
    except json.JSONDecodeError:
        log_test("Buy Asset (First)", False, "Invalid JSON response")
        return False

def test_buy_asset_second():
    """Test 6: POST /api/investments/buy - Buy BTC again (test averaging)"""
    if not btc_asset_id:
        log_test("Buy Asset (Second)", False, "No BTC asset ID available")
        return False
    
    buy_data = {
        "asset_id": btc_asset_id,
        "quantity": 0.01
    }
    
    response = make_request('POST', '/investments/buy', buy_data)
    
    if not response:
        log_test("Buy Asset (Second)", False, "Request failed")
        return False
    
    if response.status_code != 200:
        log_test("Buy Asset (Second)", False, f"Status: {response.status_code}, Response: {response.text}")
        return False
    
    try:
        data = response.json()
        
        required_fields = ['message', 'ticker', 'quantity', 'price', 'total_cost', 'new_balance']
        for field in required_fields:
            if field not in data:
                log_test("Buy Asset (Second)", False, f"Missing field: {field}")
                return False
        
        log_test("Buy Asset (Second)", True, f"Bought another {data['quantity']} {data['ticker']} for R$ {data['total_cost']:.2f}")
        return True
        
    except json.JSONDecodeError:
        log_test("Buy Asset (Second)", False, "Invalid JSON response")
        return False

def test_get_portfolio():
    """Test 7: GET /api/investments/portfolio - Get portfolio with P&L"""
    response = make_request('GET', '/investments/portfolio')
    
    if not response:
        log_test("Get Portfolio", False, "Request failed")
        return False
    
    if response.status_code != 200:
        log_test("Get Portfolio", False, f"Status: {response.status_code}, Response: {response.text}")
        return False
    
    try:
        data = response.json()
        
        required_fields = ['holdings', 'summary']
        for field in required_fields:
            if field not in data:
                log_test("Get Portfolio", False, f"Missing field: {field}")
                return False
        
        holdings = data['holdings']
        summary = data['summary']
        
        if not isinstance(holdings, list):
            log_test("Get Portfolio", False, "Holdings is not a list")
            return False
        
        # Should have at least 1 holding (BTC)
        if len(holdings) == 0:
            log_test("Get Portfolio", False, "No holdings found")
            return False
        
        # Check holding fields
        btc_holding = None
        for holding in holdings:
            if holding.get('ticker') == 'BTC':
                btc_holding = holding
                break
        
        if not btc_holding:
            log_test("Get Portfolio", False, "BTC holding not found")
            return False
        
        required_holding_fields = ['ticker', 'quantity', 'avg_price', 'current_price', 'invested', 'current_value', 'profit', 'profit_pct']
        for field in required_holding_fields:
            if field not in btc_holding:
                log_test("Get Portfolio", False, f"Missing field '{field}' in BTC holding")
                return False
        
        # Should have at least 0.02 BTC (two purchases of 0.01 each)
        if btc_holding['quantity'] < 0.02:
            log_test("Get Portfolio", False, f"Expected at least 0.02 BTC, got {btc_holding['quantity']}")
            return False
        
        # Check summary fields
        required_summary_fields = ['total_invested', 'total_current_value', 'total_profit', 'total_profit_pct', 'num_positions']
        for field in required_summary_fields:
            if field not in summary:
                log_test("Get Portfolio", False, f"Missing field '{field}' in summary")
                return False
        
        log_test("Get Portfolio", True, f"Portfolio: {summary['num_positions']} positions, Total P&L: R$ {summary['total_profit']:.2f} ({summary['total_profit_pct']:.2f}%)")
        return True
        
    except json.JSONDecodeError:
        log_test("Get Portfolio", False, "Invalid JSON response")
        return False

def test_sell_asset_partial():
    """Test 8: POST /api/investments/sell - Sell partial BTC"""
    if not btc_asset_id:
        log_test("Sell Asset (Partial)", False, "No BTC asset ID available")
        return False
    
    sell_data = {
        "asset_id": btc_asset_id,
        "quantity": 0.005
    }
    
    response = make_request('POST', '/investments/sell', sell_data)
    
    if not response:
        log_test("Sell Asset (Partial)", False, "Request failed")
        return False
    
    if response.status_code != 200:
        log_test("Sell Asset (Partial)", False, f"Status: {response.status_code}, Response: {response.text}")
        return False
    
    try:
        data = response.json()
        
        required_fields = ['message', 'ticker', 'quantity', 'price', 'total_value', 'profit', 'profit_message', 'new_balance']
        for field in required_fields:
            if field not in data:
                log_test("Sell Asset (Partial)", False, f"Missing field: {field}")
                return False
        
        if data['ticker'] != 'BTC':
            log_test("Sell Asset (Partial)", False, f"Expected BTC ticker, got {data['ticker']}")
            return False
        
        if data['quantity'] != 0.005:
            log_test("Sell Asset (Partial)", False, f"Expected quantity 0.005, got {data['quantity']}")
            return False
        
        log_test("Sell Asset (Partial)", True, f"Sold {data['quantity']} {data['ticker']} for R$ {data['total_value']:.2f}, {data['profit_message']}")
        return True
        
    except json.JSONDecodeError:
        log_test("Sell Asset (Partial)", False, "Invalid JSON response")
        return False

def test_get_transactions():
    """Test 9: GET /api/investments/transactions - Get transaction history"""
    response = make_request('GET', '/investments/transactions')
    
    if not response:
        log_test("Get Transactions", False, "Request failed")
        return False
    
    if response.status_code != 200:
        log_test("Get Transactions", False, f"Status: {response.status_code}, Response: {response.text}")
        return False
    
    try:
        transactions = response.json()
        
        if not isinstance(transactions, list):
            log_test("Get Transactions", False, "Response is not a list")
            return False
        
        # Should have at least 3 transactions (2 buys, 1 sell)
        if len(transactions) < 3:
            log_test("Get Transactions", False, f"Expected at least 3 transactions, got {len(transactions)}")
            return False
        
        # Check transaction fields
        for transaction in transactions[:3]:  # Check first 3
            required_fields = ['id', 'ticker', 'type', 'quantity', 'price', 'total', 'created_at']
            for field in required_fields:
                if field not in transaction:
                    log_test("Get Transactions", False, f"Missing field '{field}' in transaction")
                    return False
            
            if transaction['type'] not in ['buy', 'sell']:
                log_test("Get Transactions", False, f"Invalid transaction type: {transaction['type']}")
                return False
        
        # Count buy and sell transactions
        buy_count = sum(1 for t in transactions if t['type'] == 'buy')
        sell_count = sum(1 for t in transactions if t['type'] == 'sell')
        
        log_test("Get Transactions", True, f"Retrieved {len(transactions)} transactions ({buy_count} buys, {sell_count} sells)")
        return True
        
    except json.JSONDecodeError:
        log_test("Get Transactions", False, "Invalid JSON response")
        return False

def test_buy_insufficient_funds():
    """Test 10: POST /api/investments/buy - Test insufficient funds"""
    if not btc_asset_id:
        log_test("Buy Insufficient Funds", False, "No BTC asset ID available")
        return False
    
    # Try to buy 10000 BTC (should fail)
    buy_data = {
        "asset_id": btc_asset_id,
        "quantity": 10000
    }
    
    response = make_request('POST', '/investments/buy', buy_data)
    
    if not response or response.status_code == 0:
        log_test("Buy Insufficient Funds", False, "Request failed")
        return False
    
    if response.status_code != 400:
        log_test("Buy Insufficient Funds", False, f"Expected 400 status, got {response.status_code}")
        return False
    
    try:
        data = response.json()
        if 'detail' not in data:
            log_test("Buy Insufficient Funds", False, "Missing error detail")
            return False
        
        if 'insuficiente' not in data['detail'].lower():
            log_test("Buy Insufficient Funds", False, f"Expected 'insuficiente' in error message, got: {data['detail']}")
            return False
        
        log_test("Buy Insufficient Funds", True, f"Correctly rejected insufficient funds: {data['detail']}")
        return True
        
    except json.JSONDecodeError:
        log_test("Buy Insufficient Funds", False, "Invalid JSON response")
        return False

def test_sell_more_than_held():
    """Test 11: POST /api/investments/sell - Test selling more than held"""
    if not btc_asset_id:
        log_test("Sell More Than Held", False, "No BTC asset ID available")
        return False
    
    # Try to sell 1 BTC (should fail, user has less than 1 BTC)
    sell_data = {
        "asset_id": btc_asset_id,
        "quantity": 1.0
    }
    
    response = make_request('POST', '/investments/sell', sell_data)
    
    if not response or response.status_code == 0:
        log_test("Sell More Than Held", False, "Request failed")
        return False
    
    if response.status_code != 400:
        log_test("Sell More Than Held", False, f"Expected 400 status, got {response.status_code}")
        return False
    
    try:
        data = response.json()
        if 'detail' not in data:
            log_test("Sell More Than Held", False, "Missing error detail")
            return False
        
        if 'insuficiente' not in data['detail'].lower():
            log_test("Sell More Than Held", False, f"Expected 'insuficiente' in error message, got: {data['detail']}")
            return False
        
        log_test("Sell More Than Held", True, f"Correctly rejected selling more than held: {data['detail']}")
        return True
        
    except json.JSONDecodeError:
        log_test("Sell More Than Held", False, "Invalid JSON response")
        return False

def test_verify_previous_endpoints():
    """Test 12: Verify previous endpoints still work"""
    endpoints_to_test = [
        ('/user/stats', 'GET', 'User Stats'),
        ('/jobs', 'GET', 'Jobs List'),
        ('/courses', 'GET', 'Courses List')
    ]
    
    all_passed = True
    results = []
    
    for endpoint, method, name in endpoints_to_test:
        response = make_request(method, endpoint)
        
        if not response or response.status_code != 200:
            all_passed = False
            results.append(f"❌ {name}: Status {response.status_code if response else 'No response'}")
        else:
            try:
                data = response.json()
                results.append(f"✅ {name}: Working")
            except json.JSONDecodeError:
                all_passed = False
                results.append(f"❌ {name}: Invalid JSON")
    
    details = "\n   ".join(results)
    log_test("Verify Previous Endpoints", all_passed, details)
    return all_passed

def main():
    """Run all investment system tests"""
    print("=" * 70)
    print("BUSINESS EMPIRE INVESTMENT SYSTEM BACKEND TEST SUITE")
    print("Testing all investment endpoints as requested")
    print("=" * 70)
    print()
    
    tests = [
        ("User Login", test_user_login),
        ("Get Market (All Assets)", test_get_market_all),
        ("Get Market (Crypto Filter)", test_get_market_crypto),
        ("Get Market (B3 Stocks Filter)", test_get_market_acoes),
        ("Get Asset History", test_get_asset_history),
        ("Buy Asset (First)", test_buy_asset_first),
        ("Buy Asset (Second)", test_buy_asset_second),
        ("Get Portfolio", test_get_portfolio),
        ("Sell Asset (Partial)", test_sell_asset_partial),
        ("Get Transactions", test_get_transactions),
        ("Buy Insufficient Funds", test_buy_insufficient_funds),
        ("Sell More Than Held", test_sell_more_than_held),
        ("Verify Previous Endpoints", test_verify_previous_endpoints),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            log_test(test_name, False, f"Exception: {str(e)}")
            failed += 1
    
    print("=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"✅ PASSED: {passed}")
    print(f"❌ FAILED: {failed}")
    print(f"📊 TOTAL:  {passed + failed}")
    print()
    
    if failed == 0:
        print("🎉 ALL TESTS PASSED! Investment system working correctly.")
        print("✅ All 22 assets available with proper filtering")
        print("✅ Buy/sell operations working with P&L calculations")
        print("✅ Portfolio tracking and transaction history working")
        print("✅ Error handling for insufficient funds working")
        print("✅ Previous endpoints (user stats, jobs, courses) still working")
    else:
        print("⚠️  Some tests failed. Check the details above.")
        if failed > passed:
            print("❌ Major issues detected. Investment system may not be working properly.")
    
    print("=" * 70)
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)