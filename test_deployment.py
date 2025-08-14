#!/usr/bin/env python3
"""
Comprehensive Deployment Test Suite for Cloud Trading Bot

This test script validates the live deployment at cloud-trading-bot-468900.web.app
specifically focusing on the backtest endpoints that are reportedly failing with 404 errors.
"""

import requests
import json
import time
import sys
from datetime import datetime
from typing import Dict, Any, Optional

# Live deployment configuration
DEPLOYMENT_BASE_URL = "https://cloud-trading-bot-468900.web.app"
API_BASE_URL = f"{DEPLOYMENT_BASE_URL}/api"

# Local testing configuration for comparison
LOCAL_BASE_URL = "http://localhost:8080"
LOCAL_API_BASE_URL = f"{LOCAL_BASE_URL}/api"

class DeploymentTester:
    """Test suite for deployment validation"""
    
    def __init__(self, base_url: str, api_url: str, name: str):
        self.base_url = base_url
        self.api_url = api_url
        self.name = name
        self.results = []
        
    def log_result(self, test_name: str, passed: bool, details: str = ""):
        """Log test result"""
        status = "✅ PASS" if passed else "❌ FAIL"
        result = {
            'test': test_name,
            'passed': passed,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        self.results.append(result)
        print(f"{status} [{self.name}] {test_name}: {details}")
        
    def test_connectivity(self) -> bool:
        """Test basic connectivity to the deployment"""
        try:
            response = requests.get(self.base_url, timeout=10)
            self.log_result("Basic Connectivity", True, f"Status: {response.status_code}")
            return True
        except Exception as e:
            self.log_result("Basic Connectivity", False, f"Error: {str(e)}")
            return False
            
    def test_health_endpoint(self) -> bool:
        """Test the health endpoint"""
        try:
            response = requests.get(f"{self.api_url}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.log_result("Health Endpoint", True, f"Service: {data.get('service', 'unknown')}")
                return True
            else:
                self.log_result("Health Endpoint", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_result("Health Endpoint", False, f"Error: {str(e)}")
            return False
            
    def test_status_endpoint(self) -> bool:
        """Test the status endpoint"""
        try:
            response = requests.get(f"{self.api_url}/status", timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.log_result("Status Endpoint", True, f"Status: {data.get('status', 'unknown')}")
                return True
            else:
                self.log_result("Status Endpoint", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_result("Status Endpoint", False, f"Error: {str(e)}")
            return False
            
    def test_backtest_start_endpoint(self) -> Optional[str]:
        """Test the backtest start endpoint - returns job_id if successful"""
        try:
            config = {
                'symbols': ['AAPL', 'GOOGL'],
                'initial_capital': 10000,
                'short_ma_period': 5,
                'long_ma_period': 15
            }
            
            response = requests.post(
                f"{self.api_url}/backtest/start",
                json=config,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                job_id = data.get('jobId') or data.get('job_id')
                if job_id:
                    self.log_result("Backtest Start", True, f"JobID: {job_id}")
                    return job_id
                else:
                    self.log_result("Backtest Start", False, "No job ID returned")
                    return None
            else:
                self.log_result("Backtest Start", False, f"Status: {response.status_code}, Body: {response.text}")
                return None
        except Exception as e:
            self.log_result("Backtest Start", False, f"Error: {str(e)}")
            return None
            
    def test_backtest_status_endpoint(self, job_id: str) -> bool:
        """Test the backtest status endpoint"""
        try:
            response = requests.get(f"{self.api_url}/backtest/status/{job_id}", timeout=10)
            if response.status_code == 200:
                data = response.json()
                status = data.get('status', 'unknown')
                completed = data.get('completed', False)
                self.log_result("Backtest Status", True, f"Status: {status}, Completed: {completed}")
                return True
            else:
                self.log_result("Backtest Status", False, f"Status: {response.status_code}, Body: {response.text}")
                return False
        except Exception as e:
            self.log_result("Backtest Status", False, f"Error: {str(e)}")
            return False
            
    def test_backtest_results_endpoint(self, job_id: str) -> bool:
        """Test the backtest results endpoint"""
        try:
            response = requests.get(f"{self.api_url}/backtest/results/{job_id}", timeout=10)
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', {})
                metrics = results.get('metrics', {}) if results else {}
                self.log_result("Backtest Results", True, f"Trades: {metrics.get('total_trades', 0)}")
                return True
            else:
                self.log_result("Backtest Results", False, f"Status: {response.status_code}, Body: {response.text}")
                return False
        except Exception as e:
            self.log_result("Backtest Results", False, f"Error: {str(e)}")
            return False
            
    def test_backtest_workflow(self) -> bool:
        """Test the complete backtest workflow"""
        print(f"\n--- Testing complete backtest workflow for {self.name} ---")
        
        # Step 1: Start backtest
        job_id = self.test_backtest_start_endpoint()
        if not job_id:
            return False
            
        # Step 2: Check status (wait a bit for processing)
        time.sleep(2)
        status_ok = self.test_backtest_status_endpoint(job_id)
        if not status_ok:
            return False
            
        # Step 3: Wait for completion and get results
        max_wait = 30  # 30 seconds max wait
        wait_time = 0
        while wait_time < max_wait:
            try:
                response = requests.get(f"{self.api_url}/backtest/status/{job_id}", timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('completed', False):
                        break
                time.sleep(1)
                wait_time += 1
            except:
                break
                
        # Step 4: Get results
        results_ok = self.test_backtest_results_endpoint(job_id)
        return results_ok
        
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests and return summary"""
        print(f"\n{'='*60}")
        print(f"Testing {self.name} at {self.base_url}")
        print(f"{'='*60}")
        
        # Basic connectivity tests
        if not self.test_connectivity():
            return self.get_summary()
            
        # API endpoint tests
        self.test_health_endpoint()
        self.test_status_endpoint()
        
        # Backtest workflow test
        self.test_backtest_workflow()
        
        return self.get_summary()
        
    def get_summary(self) -> Dict[str, Any]:
        """Get test summary"""
        passed = sum(1 for r in self.results if r['passed'])
        total = len(self.results)
        return {
            'name': self.name,
            'total_tests': total,
            'passed_tests': passed,
            'failed_tests': total - passed,
            'success_rate': (passed / total * 100) if total > 0 else 0,
            'results': self.results
        }

def test_endpoint_availability():
    """Test availability of specific endpoints that might be missing"""
    print(f"\n{'='*60}")
    print("Testing Endpoint Availability")
    print(f"{'='*60}")
    
    endpoints_to_test = [
        "/api/health",
        "/api/status", 
        "/api/backtest/start",
        "/api/backtest/status/test",
        "/api/backtest/results/test",
        "/api/market-data",
        "/api/strategies"
    ]
    
    for base_name, base_url in [("Local", LOCAL_API_BASE_URL), ("Deployment", API_BASE_URL)]:
        print(f"\n--- {base_name} Endpoints ---")
        for endpoint in endpoints_to_test:
            try:
                url = base_url + endpoint
                response = requests.get(url, timeout=5)
                status = "✅" if response.status_code < 500 else "❌"
                print(f"{status} {endpoint}: {response.status_code}")
            except Exception as e:
                print(f"❌ {endpoint}: ERROR - {str(e)}")

def main():
    """Main test runner"""
    print("🚀 Cloud Trading Bot Deployment Test Suite")
    print(f"Testing deployment at: {DEPLOYMENT_BASE_URL}")
    print(f"Current time: {datetime.now().isoformat()}")
    
    # Test endpoint availability first
    test_endpoint_availability()
    
    # Test local setup (for comparison)
    local_tester = DeploymentTester(LOCAL_BASE_URL, LOCAL_API_BASE_URL, "Local Development")
    local_summary = local_tester.run_all_tests()
    
    # Test live deployment
    deployment_tester = DeploymentTester(DEPLOYMENT_BASE_URL, API_BASE_URL, "Live Deployment")
    deployment_summary = deployment_tester.run_all_tests()
    
    # Print final summary
    print(f"\n{'='*60}")
    print("FINAL SUMMARY")
    print(f"{'='*60}")
    
    for summary in [local_summary, deployment_summary]:
        name = summary['name']
        passed = summary['passed_tests']
        total = summary['total_tests']
        rate = summary['success_rate']
        status = "✅" if rate == 100 else "❌"
        print(f"{status} {name}: {passed}/{total} tests passed ({rate:.1f}%)")
        
        # Show failed tests
        failed_tests = [r for r in summary['results'] if not r['passed']]
        if failed_tests:
            print(f"   Failed tests:")
            for test in failed_tests:
                print(f"   - {test['test']}: {test['details']}")
    
    # Determine if issue is fixed
    deployment_backtest_tests = [r for r in deployment_summary['results'] if 'Backtest' in r['test']]
    backtest_success = all(r['passed'] for r in deployment_backtest_tests)
    
    print(f"\n{'='*60}")
    if backtest_success and deployment_backtest_tests:
        print("🎉 BACKTEST FEATURE IS WORKING ON DEPLOYMENT!")
        print("The 404 error has been resolved.")
    else:
        print("🚨 BACKTEST FEATURE STILL FAILING ON DEPLOYMENT")
        print("The 404 error persists and needs investigation.")
    print(f"{'='*60}")
    
    # Save detailed results
    results = {
        'timestamp': datetime.now().isoformat(),
        'local': local_summary,
        'deployment': deployment_summary,
        'backtest_fixed': backtest_success
    }
    
    with open('/tmp/deployment_test_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nDetailed results saved to: /tmp/deployment_test_results.json")
    
    return 0 if backtest_success else 1

if __name__ == "__main__":
    sys.exit(main())