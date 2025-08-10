"""
AWS services integration module.
Provides classes and functions to interact with AWS services.
"""
import json
import boto3
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

class AWSServicesManager:
    """Manager class for AWS services integration."""
    
    def __init__(self, region: str = 'us-east-1'):
        self.region = region
        self.dynamodb = boto3.resource('dynamodb', region_name=region)
        self.s3 = boto3.client('s3', region_name=region)
        self.secrets_manager = boto3.client('secretsmanager', region_name=region)
        self.lambda_client = boto3.client('lambda', region_name=region)
        self.ecs = boto3.client('ecs', region_name=region)
        
    def get_secret(self, secret_name: str) -> Dict[str, Any]:
        """
        Retrieve secret from AWS Secrets Manager.
        
        Args:
            secret_name: Name of the secret
            
        Returns:
            Dictionary containing secret values
        """
        try:
            response = self.secrets_manager.get_secret_value(SecretId=secret_name)
            return json.loads(response['SecretString'])
        except ClientError as e:
            logger.error(f"Error retrieving secret {secret_name}: {e}")
            return {}
    
    def store_config(self, table_name: str, config: Dict[str, Any]) -> bool:
        """
        Store configuration in DynamoDB.
        
        Args:
            table_name: DynamoDB table name
            config: Configuration dictionary
            
        Returns:
            True if successful
        """
        try:
            table = self.dynamodb.Table(table_name)
            table.put_item(
                Item={
                    'id': 'bot_config',
                    'timestamp': datetime.utcnow().isoformat(),
                    'config': json.dumps(config),
                    'updated_by': 'system'
                }
            )
            logger.info(f"Configuration stored in DynamoDB table: {table_name}")
            return True
        except Exception as e:
            logger.error(f"Error storing config in DynamoDB: {e}")
            return False
    
    def get_config(self, table_name: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve configuration from DynamoDB.
        
        Args:
            table_name: DynamoDB table name
            
        Returns:
            Configuration dictionary or None
        """
        try:
            table = self.dynamodb.Table(table_name)
            response = table.get_item(Key={'id': 'bot_config'})
            
            if 'Item' in response:
                return json.loads(response['Item']['config'])
            return None
        except Exception as e:
            logger.error(f"Error retrieving config from DynamoDB: {e}")
            return None
    
    def store_trade(self, table_name: str, trade: Dict[str, Any]) -> bool:
        """
        Store trade information in DynamoDB.
        
        Args:
            table_name: DynamoDB table name
            trade: Trade dictionary
            
        Returns:
            True if successful
        """
        try:
            table = self.dynamodb.Table(table_name)
            
            # Add trade ID and timestamp if not present
            if 'trade_id' not in trade:
                trade['trade_id'] = f"trade_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{trade.get('symbol', 'unknown')}"
            
            if 'timestamp' not in trade:
                trade['timestamp'] = datetime.utcnow().isoformat()
            
            table.put_item(Item=trade)
            logger.info(f"Trade stored: {trade['trade_id']}")
            return True
        except Exception as e:
            logger.error(f"Error storing trade in DynamoDB: {e}")
            return False
    
    def get_trades(self, table_name: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Retrieve recent trades from DynamoDB.
        
        Args:
            table_name: DynamoDB table name
            limit: Maximum number of trades to retrieve
            
        Returns:
            List of trade dictionaries
        """
        try:
            table = self.dynamodb.Table(table_name)
            response = table.scan(Limit=limit)
            
            trades = response.get('Items', [])
            # Sort by timestamp descending
            trades.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            
            return trades
        except Exception as e:
            logger.error(f"Error retrieving trades from DynamoDB: {e}")
            return []
    
    def store_logs_s3(self, bucket_name: str, log_data: str, log_type: str = 'bot') -> bool:
        """
        Store logs in S3.
        
        Args:
            bucket_name: S3 bucket name
            log_data: Log data to store
            log_type: Type of log (bot, trades, errors, etc.)
            
        Returns:
            True if successful
        """
        try:
            timestamp = datetime.utcnow()
            s3_key = f"logs/{log_type}/{timestamp.strftime('%Y/%m/%d')}/{log_type}_{timestamp.strftime('%Y%m%d_%H%M%S')}.log"
            
            self.s3.put_object(
                Bucket=bucket_name,
                Key=s3_key,
                Body=log_data,
                ContentType='text/plain'
            )
            
            logger.info(f"Logs stored in S3: s3://{bucket_name}/{s3_key}")
            return True
        except Exception as e:
            logger.error(f"Error storing logs in S3: {e}")
            return False
    
    def invoke_lambda(self, function_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Invoke AWS Lambda function.
        
        Args:
            function_name: Lambda function name
            payload: Payload to send to Lambda
            
        Returns:
            Lambda response
        """
        try:
            response = self.lambda_client.invoke(
                FunctionName=function_name,
                InvocationType='RequestResponse',
                Payload=json.dumps(payload)
            )
            
            result = json.loads(response['Payload'].read())
            logger.info(f"Lambda function {function_name} invoked successfully")
            return result
        except Exception as e:
            logger.error(f"Error invoking Lambda function {function_name}: {e}")
            return {'error': str(e)}
    
    def update_ecs_service(self, cluster_name: str, service_name: str, desired_count: int) -> bool:
        """
        Update ECS service desired count.
        
        Args:
            cluster_name: ECS cluster name
            service_name: ECS service name
            desired_count: Desired number of tasks
            
        Returns:
            True if successful
        """
        try:
            self.ecs.update_service(
                cluster=cluster_name,
                service=service_name,
                desiredCount=desired_count
            )
            
            logger.info(f"ECS service {service_name} updated to {desired_count} tasks")
            return True
        except Exception as e:
            logger.error(f"Error updating ECS service: {e}")
            return False
    
    def get_ecs_service_status(self, cluster_name: str, service_name: str) -> Dict[str, Any]:
        """
        Get ECS service status.
        
        Args:
            cluster_name: ECS cluster name
            service_name: ECS service name
            
        Returns:
            Service status information
        """
        try:
            response = self.ecs.describe_services(
                cluster=cluster_name,
                services=[service_name]
            )
            
            if response['services']:
                service = response['services'][0]
                return {
                    'status': service['status'],
                    'running_count': service['runningCount'],
                    'pending_count': service['pendingCount'],
                    'desired_count': service['desiredCount'],
                    'task_definition': service['taskDefinition']
                }
            else:
                return {'error': 'Service not found'}
        except Exception as e:
            logger.error(f"Error getting ECS service status: {e}")
            return {'error': str(e)}

# Utility functions
def create_aws_manager(region: str = None) -> AWSServicesManager:
    """
    Create and return AWS services manager.
    
    Args:
        region: AWS region (defaults to us-east-1)
        
    Returns:
        AWSServicesManager instance
    """
    if region is None:
        import os
        region = os.getenv('AWS_REGION', 'us-east-1')
    
    return AWSServicesManager(region)

def setup_cloudwatch_logging(log_group_name: str):
    """
    Set up CloudWatch logging.
    
    Args:
        log_group_name: CloudWatch log group name
    """
    try:
        import watchtower
        
        # Create CloudWatch handler
        handler = watchtower.CloudWatchLogsHandler(log_group=log_group_name)
        
        # Add to root logger
        root_logger = logging.getLogger()
        root_logger.addHandler(handler)
        
        logger.info(f"CloudWatch logging configured for log group: {log_group_name}")
    except ImportError:
        logger.warning("watchtower package not installed. CloudWatch logging not available.")
    except Exception as e:
        logger.error(f"Error setting up CloudWatch logging: {e}")