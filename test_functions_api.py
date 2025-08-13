#!/usr/bin/env python3
"""
Test script for Firebase Functions API endpoints
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from functions.main import handle_request
import json

class MockRequest:
    def __init__(self, path, method='GET', data=None, args=None):
        self.path = path
        self.method = method
        self.json_data = data
        self.args = args or {}
        self.endpoint = None  # Add endpoint attribute for Flask mode
    
    def get_json(self):
        return self.json_data

def test_endpoints():
    print("🧪 Testing Firebase Functions Endpoints")
    print("=" * 50)
    
    # Test health endpoint
    print("\n1. Testing health endpoint...")
    req = MockRequest('/api/health')
    try:
        response, status_code = handle_request(req)
        print(f"   Status: {status_code}")
        print(f"   Response: {response.get_json()}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test equity update endpoint
    print("\n2. Testing equity update endpoint...")
    req = MockRequest('/api/update-equity', 'POST', {'equity': 100000})
    try:
        response, status_code = handle_request(req)
        print(f"   Status: {status_code}")
        print(f"   Response: {response.get_json()}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test market data endpoint
    print("\n3. Testing market data endpoint...")
    req = MockRequest('/api/market-data', 'GET', args={'symbols': 'AAPL,MSFT'})
    try:
        response, status_code = handle_request(req)
        print(f"   Status: {status_code}")
        data = response.get_json()
        print(f"   Response keys: {list(data.keys())}")
        if 'error' in data:
            print(f"   Error: {data['error']}")
        else:
            print(f"   Symbols: {data.get('symbols', [])}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test unknown endpoint
    print("\n4. Testing unknown endpoint...")
    req = MockRequest('/api/unknown')
    try:
        response, status_code = handle_request(req)
        print(f"   Status: {status_code}")
        print(f"   Response: {response.get_json()}")
    except Exception as e:
        print(f"   Error: {e}")

if __name__ == "__main__":
    test_endpoints()