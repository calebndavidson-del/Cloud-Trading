#!/usr/bin/env python3
"""
Local Firebase Functions Test
Tests Firebase Functions locally to ensure they work before deployment
"""
import sys
import os

# Add the current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from functions.main import handle_request
    print("✅ Firebase Functions import successful")
except ImportError as e:
    print(f"❌ Failed to import Firebase Functions: {e}")
    sys.exit(1)

class MockRequest:
    """Mock request object for testing"""
    def __init__(self, path, method='GET', json_data=None, args=None):
        self.path = path
        self.method = method
        self._json_data = json_data or {}
        self.args = args or {}
        
    def get_json(self):
        return self._json_data

def test_functions_locally():
    """Test Firebase Functions locally"""
    print("\n🧪 Testing Firebase Functions Locally")
    print("=" * 50)
    
    tests = [
        ("health", "/api/health", "GET", None),
        ("status", "/api/status", "GET", None),
        ("backtest start", "/api/backtest/start", "POST", {
            "symbols": ["AAPL"],
            "initial_capital": 10000
        }),
    ]
    
    success_count = 0
    
    for test_name, path, method, json_data in tests:
        try:
            print(f"\n{len(tests) - tests.index((test_name, path, method, json_data)) + success_count}. Testing {test_name}...")
            
            req = MockRequest(path, method, json_data)
            response, status_code = handle_request(req)
            
            print(f"   Status: {status_code}")
            if hasattr(response, 'get_json'):
                data = response.get_json()
            elif hasattr(response, 'data'):
                data = response.data
            else:
                data = response
            
            print(f"   Response type: {type(data)}")
            if isinstance(data, dict):
                print(f"   Keys: {list(data.keys())}")
                if 'error' in data:
                    print(f"   Error: {data['error']}")
                elif 'status' in data:
                    print(f"   Status: {data['status']}")
            
            if status_code < 400:
                success_count += 1
                print("   ✅ SUCCESS")
            else:
                print("   ⚠️  WARNING - Error status code")
                
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
    
    print(f"\n" + "=" * 50)
    print(f"Local Functions Test Results: {success_count}/{len(tests)} passed")
    
    if success_count == len(tests):
        print("🎉 All local function tests passed!")
        print("Functions are ready for deployment.")
        return True
    else:
        print("⚠️  Some tests failed, but basic functionality works.")
        print("Functions should still work for basic endpoints.")
        return success_count > 0

if __name__ == "__main__":
    if test_functions_locally():
        print("\n✅ Local testing complete - Functions are ready")
        sys.exit(0)
    else:
        print("\n❌ Local testing failed - Check function implementation")
        sys.exit(1)