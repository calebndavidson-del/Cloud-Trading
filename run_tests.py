#!/usr/bin/env python3
"""
Cloud Trading Backend Test Suite Runner

This script runs the comprehensive test suite with proper configuration
and provides detailed reporting of test results and coverage.
"""
import os
import sys
import subprocess
import time
from pathlib import Path


def setup_test_environment():
    """Set up the test environment with proper configuration."""
    print("🔧 Setting up test environment...")
    
    # Set required environment variables
    os.environ['USE_MOCK_DATA'] = 'true'
    os.environ['ENVIRONMENT'] = 'test'
    os.environ['DEBUG'] = 'false'
    os.environ['TRADING_ENABLED'] = 'false'
    os.environ['PAPER_TRADING'] = 'true'
    
    # Ensure we're in the right directory
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    print("✅ Test environment configured")


def run_test_suite(test_category=None, verbose=False, coverage=False):
    """Run the test suite with specified options."""
    print(f"\n🚀 Running test suite...")
    
    # Build pytest command
    cmd = ['python', '-m', 'pytest']
    
    if test_category:
        if test_category in ['smoke', 'integration', 'e2e', 'performance', 'slow']:
            cmd.extend(['-m', test_category])
        else:
            cmd.append(f'tests/{test_category}/')
    
    if verbose:
        cmd.append('-v')
    
    if coverage:
        cmd.extend(['--cov=backend', '--cov=api', '--cov-report=term-missing', '--cov-report=html'])
    
    # Add timing and formatting options
    cmd.extend(['--tb=short', '-ra'])
    
    print(f"Running: {' '.join(cmd)}")
    
    start_time = time.time()
    result = subprocess.run(cmd, capture_output=False)
    end_time = time.time()
    
    duration = end_time - start_time
    print(f"\n⏱️  Test execution completed in {duration:.2f} seconds")
    
    return result.returncode == 0


def run_smoke_tests():
    """Run quick smoke tests."""
    print("\n💨 Running smoke tests (quick validation)...")
    return run_test_suite('smoke', verbose=True)


def run_integration_tests():
    """Run integration tests."""
    print("\n🔗 Running integration tests...")
    return run_test_suite('integration', verbose=True)


def run_performance_tests():
    """Run performance tests."""
    print("\n⚡ Running performance tests...")
    return run_test_suite('performance', verbose=True)


def run_full_suite():
    """Run the complete test suite with coverage."""
    print("\n🎯 Running complete test suite with coverage...")
    return run_test_suite(coverage=True, verbose=True)


def validate_installation():
    """Validate that all required packages are installed."""
    print("📦 Validating installation...")
    
    required_packages = [
        'pytest', 'flask', 'yfinance', 'pandas', 'numpy', 
        'optuna', 'sklearn', 'requests'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing packages: {', '.join(missing_packages)}")
        print("Please install with: pip install -r requirements_Version9.txt")
        return False
    
    print("✅ All required packages installed")
    return True


def check_backend_modules():
    """Check that backend modules can be imported."""
    print("🔍 Checking backend modules...")
    
    try:
        # Add project root to Python path
        sys.path.insert(0, str(Path.cwd()))
        
        from backend.data_collector import fetch_market_data
        from backend.optimizer import optimize_strategy
        from backend.paper_trader import paper_trade
        from backend.config import get_config
        from api import app
        
        print("✅ All backend modules importable")
        return True
    
    except ImportError as e:
        print(f"❌ Backend module import error: {e}")
        return False


def generate_test_report():
    """Generate a comprehensive test report."""
    print("\n📊 Generating test report...")
    
    # Run tests with detailed output and coverage
    cmd = [
        'python', '-m', 'pytest', 
        '--cov=backend', 
        '--cov=api',
        '--cov-report=html',
        '--cov-report=term',
        '--html=test-report.html',
        '--self-contained-html',
        '-v'
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Test report generated successfully")
            print("📄 HTML report: test-report.html")
            print("📄 Coverage report: htmlcov/index.html")
        else:
            print(f"⚠️  Test report generation completed with issues")
            print(result.stdout)
            if result.stderr:
                print("Errors:", result.stderr)
        
        return result.returncode == 0
    
    except FileNotFoundError:
        print("❌ pytest-html not installed. Install with: pip install pytest-html")
        return False


def main():
    """Main test runner function."""
    print("=" * 60)
    print("🧪 Cloud Trading Backend Test Suite")
    print("=" * 60)
    
    # Validate environment
    if not validate_installation():
        sys.exit(1)
    
    if not check_backend_modules():
        sys.exit(1)
    
    # Setup test environment
    setup_test_environment()
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        test_type = sys.argv[1].lower()
        
        if test_type == 'smoke':
            success = run_smoke_tests()
        elif test_type == 'integration':
            success = run_integration_tests()
        elif test_type == 'performance':
            success = run_performance_tests()
        elif test_type == 'full':
            success = run_full_suite()
        elif test_type == 'report':
            success = generate_test_report()
        else:
            print(f"❌ Unknown test type: {test_type}")
            print("Available options: smoke, integration, performance, full, report")
            sys.exit(1)
    else:
        # Default: run smoke tests first, then full suite if they pass
        print("🎯 Running default test sequence...")
        
        if run_smoke_tests():
            print("\n✅ Smoke tests passed! Running full test suite...")
            success = run_full_suite()
        else:
            print("\n❌ Smoke tests failed! Skipping full suite.")
            success = False
    
    # Summary
    print("\n" + "=" * 60)
    if success:
        print("🎉 Test suite completed successfully!")
        print("✅ All tests passed - system is ready for deployment")
    else:
        print("❌ Test suite completed with failures")
        print("⚠️  Please review and fix failing tests")
    print("=" * 60)
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()