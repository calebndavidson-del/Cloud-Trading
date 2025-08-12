#!/usr/bin/env python3
"""
Smoke tests for deployed infrastructure.
"""
import sys
import os
import requests
import time
import argparse
import boto3
from botocore.exceptions import ClientError


def test_lambda_functions(environment):
    """Test Lambda functions are deployed and accessible."""
    print(f"🔍 Testing Lambda functions in {environment}...")
    
    try:
        lambda_client = boto3.client('lambda')
        
        # List functions with our naming pattern
        function_prefix = f"cloud-trading-{environment}"
        
        response = lambda_client.list_functions()
        our_functions = [f for f in response['Functions'] 
                        if f['FunctionName'].startswith(function_prefix)]
        
        if not our_functions:
            print(f"❌ No Lambda functions found with prefix {function_prefix}")
            return False
        
        print(f"✅ Found {len(our_functions)} Lambda functions")
        
        # Test invoke one function
        for func in our_functions[:1]:  # Test first function
            try:
                test_payload = {"test": True, "symbols": ["AAPL"]}
                
                response = lambda_client.invoke(
                    FunctionName=func['FunctionName'],
                    InvocationType='RequestResponse',
                    Payload=str(test_payload).encode()
                )
                
                if response['StatusCode'] == 200:
                    print(f"✅ Lambda function {func['FunctionName']} responds correctly")
                else:
                    print(f"❌ Lambda function {func['FunctionName']} returned status {response['StatusCode']}")
                    return False
                    
            except Exception as e:
                print(f"❌ Error testing Lambda function {func['FunctionName']}: {e}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing Lambda functions: {e}")
        return False


def test_dynamodb_tables(environment):
    """Test DynamoDB tables are accessible."""
    print(f"🔍 Testing DynamoDB tables in {environment}...")
    
    try:
        dynamodb = boto3.client('dynamodb')
        
        # List tables with our naming pattern
        table_prefix = f"cloud-trading-{environment}"
        
        response = dynamodb.list_tables()
        our_tables = [t for t in response['TableNames'] 
                     if t.startswith(table_prefix)]
        
        if not our_tables:
            print(f"❌ No DynamoDB tables found with prefix {table_prefix}")
            return False
        
        print(f"✅ Found {len(our_tables)} DynamoDB tables")
        
        # Test table accessibility
        for table_name in our_tables[:1]:  # Test first table
            try:
                response = dynamodb.describe_table(TableName=table_name)
                
                if response['Table']['TableStatus'] == 'ACTIVE':
                    print(f"✅ DynamoDB table {table_name} is active")
                else:
                    print(f"❌ DynamoDB table {table_name} status: {response['Table']['TableStatus']}")
                    return False
                    
            except Exception as e:
                print(f"❌ Error accessing DynamoDB table {table_name}: {e}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing DynamoDB tables: {e}")
        return False


def test_s3_buckets(environment):
    """Test S3 buckets are accessible."""
    print(f"🔍 Testing S3 buckets in {environment}...")
    
    try:
        s3_client = boto3.client('s3')
        
        # List buckets with our naming pattern
        bucket_prefix = f"cloud-trading-{environment}"
        
        response = s3_client.list_buckets()
        our_buckets = [b['Name'] for b in response['Buckets'] 
                      if b['Name'].startswith(bucket_prefix)]
        
        if not our_buckets:
            print(f"❌ No S3 buckets found with prefix {bucket_prefix}")
            return False
        
        print(f"✅ Found {len(our_buckets)} S3 buckets")
        
        # Test bucket accessibility
        for bucket_name in our_buckets[:1]:  # Test first bucket
            try:
                s3_client.head_bucket(Bucket=bucket_name)
                print(f"✅ S3 bucket {bucket_name} is accessible")
                
            except Exception as e:
                print(f"❌ Error accessing S3 bucket {bucket_name}: {e}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing S3 buckets: {e}")
        return False


def test_api_endpoints(environment):
    """Test API endpoints if they exist."""
    print(f"🔍 Testing API endpoints in {environment}...")
    
    # This would test API Gateway endpoints if they exist
    # For now, just return True as we don't have API Gateway in this setup
    print("✅ No API endpoints to test in current setup")
    return True


def test_monitoring_and_logging(environment):
    """Test CloudWatch monitoring and logging."""
    print(f"🔍 Testing monitoring and logging in {environment}...")
    
    try:
        cloudwatch = boto3.client('cloudwatch')
        logs_client = boto3.client('logs')
        
        # Check for log groups
        log_group_prefix = f"/aws/lambda/cloud-trading-{environment}"
        
        response = logs_client.describe_log_groups(
            logGroupNamePrefix=log_group_prefix
        )
        
        if response['logGroups']:
            print(f"✅ Found {len(response['logGroups'])} CloudWatch log groups")
        else:
            print(f"⚠️  No CloudWatch log groups found with prefix {log_group_prefix}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing monitoring and logging: {e}")
        return False


def run_smoke_tests(environment):
    """Run all smoke tests."""
    print(f"🚀 Running smoke tests for {environment} environment...")
    print("=" * 60)
    
    tests = [
        ("Lambda Functions", test_lambda_functions),
        ("DynamoDB Tables", test_dynamodb_tables),
        ("S3 Buckets", test_s3_buckets),
        ("API Endpoints", test_api_endpoints),
        ("Monitoring & Logging", test_monitoring_and_logging),
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 30)
        
        try:
            if test_func(environment):
                passed_tests += 1
            else:
                print(f"❌ {test_name} test failed")
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")
    
    # Summary
    print("\n" + "=" * 60)
    print(f"Smoke Test Summary: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All smoke tests passed!")
        return True
    else:
        print("❌ Some smoke tests failed!")
        return False


def main():
    parser = argparse.ArgumentParser(description='Run smoke tests for deployed infrastructure')
    parser.add_argument('--environment', default='staging', 
                       help='Environment to test (staging/prod)')
    
    args = parser.parse_args()
    
    # Validate AWS credentials are available
    try:
        boto3.client('sts').get_caller_identity()
    except Exception as e:
        print(f"❌ AWS credentials not configured: {e}")
        sys.exit(1)
    
    success = run_smoke_tests(args.environment)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()