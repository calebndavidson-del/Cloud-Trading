"""
Configuration, secrets, and cloud environment variables.
"""
import os
from typing import Dict, Any

# Environment Configuration
ENV = os.getenv("ENV", "development")
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

# API Keys and Secrets
YAHOO_API_KEY = os.getenv("YAHOO_API_KEY", "")
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY", "")

# AWS Configuration
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
AWS_PROFILE = os.getenv("AWS_PROFILE", "default")

# DynamoDB Tables
DYNAMODB_CONFIG_TABLE = os.getenv("DYNAMODB_CONFIG_TABLE", "trading-bot-config")
DYNAMODB_STATE_TABLE = os.getenv("DYNAMODB_STATE_TABLE", "trading-bot-state")
DYNAMODB_TRADES_TABLE = os.getenv("DYNAMODB_TRADES_TABLE", "trading-bot-trades")

# S3 Configuration
S3_BUCKET_LOGS = os.getenv("S3_BUCKET_LOGS", "trading-bot-logs")
S3_BUCKET_DATA = os.getenv("S3_BUCKET_DATA", "trading-bot-data")

# Secrets Manager
SECRETS_MANAGER_ARN = os.getenv("SECRETS_MANAGER_ARN", "")

# Lambda Configuration
LAMBDA_FUNCTION_NAME = os.getenv("LAMBDA_FUNCTION_NAME", "trading-bot-data-fetcher")

# ECS Configuration
ECS_CLUSTER_NAME = os.getenv("ECS_CLUSTER_NAME", "trading-bot-cluster")
ECS_SERVICE_NAME = os.getenv("ECS_SERVICE_NAME", "trading-bot-strategy")
ECS_TASK_DEFINITION = os.getenv("ECS_TASK_DEFINITION", "trading-bot-strategy-task")

# Trading Configuration
DEFAULT_SYMBOLS = ["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN", "META", "NVDA", "NFLX"]
TRADING_ENABLED = os.getenv("TRADING_ENABLED", "false").lower() == "true"
PAPER_TRADING = os.getenv("PAPER_TRADING", "true").lower() == "true"

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

def get_config() -> Dict[str, Any]:
    """
    Get complete configuration dictionary.
    
    Returns:
        Dictionary containing all configuration values
    """
    return {
        "env": ENV,
        "debug": DEBUG,
        "aws": {
            "region": AWS_REGION,
            "profile": AWS_PROFILE,
            "dynamodb": {
                "config_table": DYNAMODB_CONFIG_TABLE,
                "state_table": DYNAMODB_STATE_TABLE,
                "trades_table": DYNAMODB_TRADES_TABLE
            },
            "s3": {
                "logs_bucket": S3_BUCKET_LOGS,
                "data_bucket": S3_BUCKET_DATA
            },
            "secrets_manager_arn": SECRETS_MANAGER_ARN,
            "lambda": {
                "function_name": LAMBDA_FUNCTION_NAME
            },
            "ecs": {
                "cluster_name": ECS_CLUSTER_NAME,
                "service_name": ECS_SERVICE_NAME,
                "task_definition": ECS_TASK_DEFINITION
            }
        },
        "trading": {
            "default_symbols": DEFAULT_SYMBOLS,
            "enabled": TRADING_ENABLED,
            "paper_trading": PAPER_TRADING
        },
        "logging": {
            "level": LOG_LEVEL,
            "format": LOG_FORMAT
        }
    }