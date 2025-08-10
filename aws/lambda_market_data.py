"""
AWS Lambda function for market data fetching.
This function can be deployed as a serverless AWS Lambda to fetch market data periodically.
"""
import json
import logging
import boto3
from datetime import datetime
from typing import Dict, Any

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    AWS Lambda handler for market data fetching.
    
    Args:
        event: Lambda event data
        context: Lambda context
    
    Returns:
        Response with market data and status
    """
    try:
        # Import here to reduce cold start time
        import sys
        import os
        
        # Add the backend modules to path
        sys.path.append('/opt')
        sys.path.append('/var/task')
        
        from backend.data_collector import fetch_market_data, fetch_market_trends
        from backend.config import get_config
        
        logger.info(f"Processing market data fetch request: {event}")
        
        # Get configuration
        config = get_config()
        
        # Get symbols from event or use defaults
        symbols = event.get('symbols', config['trading']['default_symbols'])
        
        # Fetch market data
        market_data = fetch_market_data(symbols, use_mock=False)
        
        # Fetch market trends
        trends = fetch_market_trends()
        
        # Prepare response
        response_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'market_data': market_data,
            'trends': trends,
            'symbols_processed': len(symbols)
        }
        
        # Store data in DynamoDB if configured
        if not config.get('debug', False):
            store_market_data_dynamodb(response_data, config)
        
        # Store data in S3 if configured
        store_market_data_s3(response_data, config)
        
        return {
            'statusCode': 200,
            'body': json.dumps(response_data, default=str),
            'headers': {
                'Content-Type': 'application/json'
            }
        }
        
    except Exception as e:
        logger.error(f"Error in Lambda function: {str(e)}")
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }),
            'headers': {
                'Content-Type': 'application/json'
            }
        }

def store_market_data_dynamodb(data: Dict[str, Any], config: Dict[str, Any]):
    """Store market data in DynamoDB."""
    try:
        dynamodb = boto3.resource('dynamodb', region_name=config['aws']['region'])
        table_name = config['aws']['dynamodb']['state_table']
        table = dynamodb.Table(table_name)
        
        # Store current market state
        table.put_item(
            Item={
                'id': f"market_data_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                'timestamp': data['timestamp'],
                'market_data': json.dumps(data['market_data']),
                'trends': json.dumps(data['trends']),
                'ttl': int((datetime.utcnow().timestamp() + 86400 * 7))  # 7 days TTL
            }
        )
        
        logger.info(f"Stored market data in DynamoDB table: {table_name}")
        
    except Exception as e:
        logger.error(f"Error storing data in DynamoDB: {e}")

def store_market_data_s3(data: Dict[str, Any], config: Dict[str, Any]):
    """Store market data in S3."""
    try:
        s3 = boto3.client('s3', region_name=config['aws']['region'])
        bucket_name = config['aws']['s3']['data_bucket']
        
        # Create S3 key with date partitioning
        timestamp = datetime.utcnow()
        s3_key = f"market_data/{timestamp.strftime('%Y/%m/%d')}/market_data_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        
        # Upload to S3
        s3.put_object(
            Bucket=bucket_name,
            Key=s3_key,
            Body=json.dumps(data, default=str, indent=2),
            ContentType='application/json'
        )
        
        logger.info(f"Stored market data in S3: s3://{bucket_name}/{s3_key}")
        
    except Exception as e:
        logger.error(f"Error storing data in S3: {e}")

# For local testing
if __name__ == "__main__":
    import os
    os.environ['USE_MOCK_DATA'] = 'true'
    
    test_event = {
        'symbols': ['AAPL', 'GOOGL', 'MSFT']
    }
    
    class MockContext:
        function_name = "test-market-data-fetcher"
        function_version = "1.0"
        aws_request_id = "test-request-id"
    
    result = lambda_handler(test_event, MockContext())
    print(json.dumps(result, indent=2))