#!/usr/bin/env python3
"""
Test script to validate Lambda deployment package structure and imports.
This ensures the optimized package will work correctly in AWS Lambda.
"""
import sys
import os
import tempfile
import zipfile
import subprocess
from pathlib import Path

def test_lambda_package():
    """Test the Lambda deployment package structure and dependencies."""
    print("🧪 Testing Lambda deployment package...")
    
    # Get the repository root
    repo_root = Path(__file__).parent.parent
    terraform_dir = repo_root / "infrastructure" / "terraform"
    
    # Check if lambda_deployment.zip exists
    zip_path = terraform_dir / "lambda_deployment.zip"
    if not zip_path.exists():
        print(f"❌ lambda_deployment.zip not found at {zip_path}")
        print("   Run './scripts/deploy.sh' to create the package first")
        return False
    
    print(f"✅ Found lambda_deployment.zip ({zip_path.stat().st_size / 1024:.1f} KB)")
    
    # Create temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Extract the zip file
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_path)
        
        # Check required directories exist
        required_dirs = ['backend', 'aws']
        for dir_name in required_dirs:
            dir_path = temp_path / dir_name
            if not dir_path.exists():
                print(f"❌ Required directory '{dir_name}' not found in package")
                return False
            print(f"✅ Found {dir_name}/ directory")
        
        # Check required files exist
        required_files = [
            'aws/lambda_market_data.py',
            'backend/data_collector.py',
            'backend/config.py',
            'requirements.txt'
        ]
        
        for file_path in required_files:
            full_path = temp_path / file_path
            if not full_path.exists():
                print(f"❌ Required file '{file_path}' not found in package")
                return False
            print(f"✅ Found {file_path}")
        
        # Test Python imports (simulate Lambda environment)
        print("\n🔍 Testing Python imports...")
        test_script = temp_path / "test_imports.py"
        
        test_content = """
import sys
import os

# Simulate Lambda environment paths
sys.path.insert(0, '/var/task')
sys.path.insert(0, '/opt')

try:
    # Test basic Python imports
    import json
    import logging
    from datetime import datetime
    from typing import Dict, Any
    print("✅ Basic Python modules imported successfully")
    
    # Test Lambda function import
    from aws.lambda_market_data import lambda_handler
    print("✅ Lambda handler imported successfully")
    
    # Test backend imports
    from backend.config import get_config
    print("✅ Backend config imported successfully")
    
    # Test that the lambda handler can be called with mock data
    mock_event = {'symbols': ['AAPL', 'MSFT']}
    
    class MockContext:
        function_name = "test-function"
        aws_request_id = "test-request"
    
    # Set mock environment to avoid real API calls
    os.environ['USE_MOCK_DATA'] = 'true'
    
    result = lambda_handler(mock_event, MockContext())
    print(f"✅ Lambda handler executed successfully: {result.get('statusCode', 'unknown')}")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Runtime error: {e}")
    sys.exit(1)

print("✅ All tests passed!")
"""
        
        test_script.write_text(test_content)
        
        # Run the test script
        try:
            result = subprocess.run([
                sys.executable, str(test_script)
            ], cwd=temp_path, capture_output=True, text=True, timeout=30)
            
            print(result.stdout)
            if result.stderr:
                print("⚠️  Warnings:", result.stderr)
            
            if result.returncode != 0:
                print(f"❌ Test script failed with return code {result.returncode}")
                return False
                
        except subprocess.TimeoutExpired:
            print("❌ Test script timed out")
            return False
        except Exception as e:
            print(f"❌ Error running test script: {e}")
            return False
    
    return True

def main():
    """Main test function."""
    print("🚀 Lambda Package Validation Test")
    print("=" * 50)
    
    success = test_lambda_package()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 All tests passed! Lambda package is ready for deployment.")
        print("\nNext steps:")
        print("1. Run './scripts/deploy.sh' to deploy the infrastructure")
        print("2. The Lambda function will be deployed via S3, avoiding size limits")
        print("3. Monitor CloudWatch logs for Lambda execution")
    else:
        print("❌ Tests failed. Please check the package structure and dependencies.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())