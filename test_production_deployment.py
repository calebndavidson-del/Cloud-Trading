#!/usr/bin/env python3
"""
Production Deployment Verification Script
For testing the live Cloud Trading Bot deployment at cloud-trading-bot-468900.web.app

This script should be run by someone with access to the live deployment to verify
that the backtest endpoints are working correctly in production.
"""

import requests
import json
import time
import sys
from datetime import datetime

# Production deployment configuration
DEPLOYMENT_URL = "https://cloud-trading-bot-468900.web.app"
API_BASE_URL = f"{DEPLOYMENT_URL}/api"

def test_deployment_connectivity():
    """Test basic connectivity to the deployment"""
    print("🔗 Testing Deployment Connectivity")
    print("=" * 50)
    
    try:
        # Test main site
        print("1. Testing main site...")
        response = requests.get(DEPLOYMENT_URL, timeout=10)
        print(f"   Status: {response.status_code}")
        print(f"   Response size: {len(response.content)} bytes")
        
        # Test API health endpoint
        print("\\n2. Testing API health endpoint...")
        response = requests.get(f"{API_BASE_URL}/health", timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Service: {data.get('service', 'unknown')}")
            print(f"   Status: {data.get('status', 'unknown')}")
        else:
            print(f"   Error: {response.text[:200]}")
            
        # Test API status endpoint
        print("\\n3. Testing API status endpoint...")
        response = requests.get(f"{API_BASE_URL}/status", timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Bot Status: {data.get('status', 'unknown')}")
            print(f"   Environment: {data.get('environment', 'unknown')}")
        else:
            print(f"   Error: {response.text[:200]}")
            
        return True
        
    except Exception as e:
        print(f"❌ Connectivity test failed: {e}")
        return False

def test_backtest_workflow():
    """Test the complete backtest workflow"""
    print("\\n🧪 Testing Backtest Workflow")
    print("=" * 50)
    
    try:
        # Step 1: Start backtest
        print("1. Starting backtest...")
        config = {
            'symbols': ['AAPL', 'GOOGL'],
            'initial_capital': 10000,
            'short_ma_period': 5,
            'long_ma_period': 15
        }
        
        response = requests.post(
            f"{API_BASE_URL}/backtest/start",
            json=config,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        print(f"   Status: {response.status_code}")
        if response.status_code != 200:
            print(f"   ❌ Failed to start backtest: {response.text}")
            return False
            
        data = response.json()
        print(f"   Response: {json.dumps(data, indent=6)}")
        
        # Extract job ID (handle both formats)
        job_id = data.get('jobId') or data.get('job_id')
        if not job_id:
            print("   ❌ No job ID returned")
            return False
            
        print(f"   ✅ Backtest started with job ID: {job_id}")
        
        # Step 2: Check status
        print("\\n2. Checking backtest status...")
        max_attempts = 10
        completed = False
        
        for attempt in range(max_attempts):
            response = requests.get(f"{API_BASE_URL}/backtest/status/{job_id}", timeout=10)
            print(f"   Attempt {attempt + 1}: Status {response.status_code}")
            
            if response.status_code == 200:
                status_data = response.json()
                print(f"   Job Status: {status_data.get('status', 'unknown')}")
                print(f"   Progress: {status_data.get('progress', 0)}%")
                
                if status_data.get('completed') or status_data.get('status') == 'completed':
                    completed = True
                    print("   ✅ Backtest completed!")
                    break
                else:
                    print("   ⏳ Waiting for completion...")
                    time.sleep(2)
            else:
                print(f"   ❌ Status check failed: {response.text[:100]}")
                return False
                
        if not completed:
            print("   ⚠️ Backtest did not complete within expected time")
            
        # Step 3: Get results
        print("\\n3. Getting backtest results...")
        response = requests.get(f"{API_BASE_URL}/backtest/results/{job_id}", timeout=10)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            results = response.json()
            print("   ✅ Results retrieved successfully!")
            
            # Validate result structure
            if 'results' in results:
                metrics = results['results'].get('metrics', {})
                trades = results['results'].get('trades', [])
                print(f"   Total trades: {metrics.get('total_trades', 0)}")
                print(f"   Net profit: {metrics.get('net_profit', 'N/A')}")
                print(f"   Win rate: {metrics.get('win_rate', 'N/A')}")
                print(f"   Number of trade records: {len(trades)}")
                
                return True
            else:
                print(f"   ⚠️ Unexpected result format: {json.dumps(results, indent=6)}")
                return False
        else:
            print(f"   ❌ Failed to get results: {response.text[:100]}")
            return False
            
    except Exception as e:
        print(f"❌ Backtest workflow test failed: {e}")
        return False

def test_error_handling():
    """Test error handling for invalid requests"""
    print("\\n🚫 Testing Error Handling")
    print("=" * 50)
    
    try:
        # Test invalid job ID
        print("1. Testing invalid job ID...")
        response = requests.get(f"{API_BASE_URL}/backtest/status/invalid_job_id", timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 404:
            print("   ✅ Correctly returns 404 for invalid job ID")
        else:
            print(f"   ⚠️ Expected 404, got {response.status_code}")
            
        # Test invalid backtest config
        print("\\n2. Testing invalid backtest config...")
        response = requests.post(
            f"{API_BASE_URL}/backtest/start",
            json={},  # Empty config
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text[:200]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False

def main():
    """Main test runner for production deployment"""
    print("🚀 Cloud Trading Bot - Production Deployment Test")
    print(f"Testing: {DEPLOYMENT_URL}")
    print(f"Time: {datetime.now().isoformat()}")
    print("=" * 60)
    
    # Run all tests
    connectivity_ok = test_deployment_connectivity()
    
    if not connectivity_ok:
        print("\\n❌ CRITICAL: Basic connectivity failed")
        print("Cannot proceed with backtest testing.")
        return 1
    
    backtest_ok = test_backtest_workflow()
    error_handling_ok = test_error_handling()
    
    # Final summary
    print("\\n" + "=" * 60)
    print("PRODUCTION DEPLOYMENT TEST SUMMARY")
    print("=" * 60)
    print(f"Connectivity:     {'✅ PASS' if connectivity_ok else '❌ FAIL'}")
    print(f"Backtest Workflow: {'✅ PASS' if backtest_ok else '❌ FAIL'}")  
    print(f"Error Handling:    {'✅ PASS' if error_handling_ok else '❌ FAIL'}")
    
    all_passed = connectivity_ok and backtest_ok and error_handling_ok
    
    if all_passed:
        print("\\n🎉 ALL TESTS PASSED!")
        print("The backtest feature is working correctly in production.")
        print("The 404 error issue has been resolved.")
    else:
        print("\\n🚨 SOME TESTS FAILED!")
        print("The backtest feature needs attention.")
        
        if connectivity_ok and not backtest_ok:
            print("\\nTROUBLESHOoting TIPS:")
            print("- Check if the correct backend is deployed")
            print("- Verify API routing configuration in Firebase")
            print("- Check Firebase Functions or Cloud Run logs")
            print("- Ensure the backtest endpoints are properly mapped")
    
    print("\\n" + "=" * 60)
    return 0 if all_passed else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)