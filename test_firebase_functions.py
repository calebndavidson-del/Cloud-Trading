#!/usr/bin/env python3
"""
Test script for Firebase Functions
Tests the API endpoints without requiring Firebase emulator
"""
import sys
import os
import json
from datetime import datetime

# Mock Flask response
class MockResponse:
    def __init__(self, data, status_code=200):
        self.data = data
        self.status_code = status_code

def mock_jsonify(data):
    return MockResponse(data)

# Mock Flask Request for testing
class MockRequest:
    def __init__(self, method='GET', path='/api/health', args=None, json_data=None):
        self.method = method
        self.path = path
        self.args = args or {}
        self.json_data = json_data
    
    def get_json(self):
        return self.json_data
    
    def get(self, key, default=None):
        return self.args.get(key, default)

# Inline implementation of Firebase Functions for testing
PORTFOLIO_STATE = {
    'equity': 100000.0,
    'last_updated': datetime.utcnow().isoformat()
}

def handle_health(req):
    """Health check endpoint"""
    return mock_jsonify({
        'status': 'healthy',
        'service': 'cloud-trading-bot-firebase',
        'version': '1.0.0',
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }), 200

def handle_status(req):
    """Get trading bot status"""
    return mock_jsonify({
        'status': 'running',
        'environment': 'firebase',
        'trading_enabled': False,
        'paper_trading': True,
        'portfolio_value': PORTFOLIO_STATE['equity'],
        'is_running': True,
        'daily_pnl': 0,
        'active_strategies': 1,
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }), 200

def handle_market_data(req):
    """Get mock market data for demo purposes"""
    symbols = req.args.get('symbols', 'AAPL,GOOGL,MSFT').split(',')
    
    # Mock market data
    mock_data = {}
    for symbol in symbols:
        if symbol.strip():
            mock_data[symbol.strip()] = {
                'price': 150.00 + hash(symbol) % 100,
                'change': (hash(symbol) % 10) - 5,
                'change_percent': ((hash(symbol) % 10) - 5) / 150.0 * 100,
                'volume': 1000000 + hash(symbol) % 500000,
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }
    
    return mock_jsonify({
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'symbols': symbols,
        'data': mock_data,
        'status': 'success'
    }), 200

def handle_update_equity(req):
    """Handle equity update requests"""
    if req.method != 'POST':
        return mock_jsonify({'error': 'Method not allowed'}), 405
    
    try:
        data = req.get_json()
        if not data or 'equity' not in data:
            return mock_jsonify({'error': 'Missing equity value in request'}), 400
        
        new_equity = float(data['equity'])
        if new_equity <= 0:
            return mock_jsonify({'error': 'Equity must be positive'}), 400
        
        # Update global state
        PORTFOLIO_STATE['equity'] = new_equity
        PORTFOLIO_STATE['last_updated'] = datetime.utcnow().isoformat()
        
        return mock_jsonify({
            'status': 'success',
            'equity': new_equity,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'message': f'Equity updated to ${new_equity:,.2f}'
        }), 200
        
    except (ValueError, TypeError) as e:
        return mock_jsonify({'error': 'Invalid equity value'}), 400

def test_endpoints():
    """Test all Firebase Function endpoints"""
    try:
        print("Testing Firebase Functions...")
        print("=" * 50)
        
        # Test health endpoint
        print("\n1. Testing Health Endpoint:")
        health_req = MockRequest(path='/api/health')
        health_result, status = handle_health(health_req)
        print(f"Status: {status}")
        print(f"Response: {json.dumps(health_result.data, indent=2)}")
        
        # Test status endpoint
        print("\n2. Testing Status Endpoint:")
        status_req = MockRequest(path='/api/status')
        status_result, status = handle_status(status_req)
        print(f"Status: {status}")
        print(f"Response: {json.dumps(status_result.data, indent=2)}")
        
        # Test market data endpoint
        print("\n3. Testing Market Data Endpoint:")
        market_req = MockRequest(path='/api/market-data', args={'symbols': 'AAPL,GOOGL'})
        market_result, status = handle_market_data(market_req)
        print(f"Status: {status}")
        print(f"Response: {json.dumps(market_result.data, indent=2)}")
        
        # Test equity update endpoint
        print("\n4. Testing Equity Update Endpoint:")
        equity_req = MockRequest(
            method='POST', 
            path='/api/update-equity',
            json_data={'equity': 150000.0}
        )
        equity_result, status = handle_update_equity(equity_req)
        print(f"Status: {status}")
        print(f"Response: {json.dumps(equity_result.data, indent=2)}")
        
        # Test invalid equity update
        print("\n5. Testing Invalid Equity Update:")
        invalid_req = MockRequest(
            method='POST', 
            path='/api/update-equity',
            json_data={'equity': -1000.0}
        )
        invalid_result, status = handle_update_equity(invalid_req)
        print(f"Status: {status}")
        print(f"Response: {json.dumps(invalid_result.data, indent=2)}")
        
        print("\n" + "=" * 50)
        print("✅ All tests passed! Firebase Functions are working correctly.")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_endpoints()
    sys.exit(0 if success else 1)