"""
Configuration, secrets, and cloud environment variables.
Supports both AWS (legacy) and modern cloud platforms.
"""
import os
from typing import Dict, Any

# Environment Configuration
ENV = os.getenv("ENVIRONMENT", os.getenv("ENV", "development"))
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
USE_MOCK_DATA = os.getenv("USE_MOCK_DATA", "true").lower() == "true"

# API Keys and Secrets
YAHOO_API_KEY = os.getenv("YAHOO_API_KEY", "")
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY", "")

# AWS Configuration (Legacy - for backward compatibility)
AWS_REGION = os.getenv("AWS_REGION", "us-west-2")
AWS_PROFILE = os.getenv("AWS_PROFILE", "default")

# DynamoDB Tables (Legacy)
DYNAMODB_CONFIG_TABLE = os.getenv("DYNAMODB_CONFIG_TABLE", "trading-bot-config")
DYNAMODB_STATE_TABLE = os.getenv("DYNAMODB_STATE_TABLE", "trading-bot-state")
DYNAMODB_TRADES_TABLE = os.getenv("DYNAMODB_TRADES_TABLE", "trading-bot-trades")

# S3 Configuration (Legacy)
S3_BUCKET_LOGS = os.getenv("S3_BUCKET_LOGS", "cloud-trading-bot-lambda-deployment-m6x4p8e")
S3_BUCKET_DATA = os.getenv("S3_BUCKET_DATA", "cloud-trading-bot-lambda-deployment-m6x4p8e")

# S3 Key Prefixes for organization within the single bucket
S3_PREFIX_LOGS = "logs/"
S3_PREFIX_DATA = "data/"
S3_PREFIX_LAMBDA = "lambda/"

# Secrets Manager (Legacy)
SECRETS_MANAGER_ARN = os.getenv("SECRETS_MANAGER_ARN", "")

# Lambda Configuration (Legacy)
LAMBDA_FUNCTION_NAME = os.getenv("LAMBDA_FUNCTION_NAME", "trading-bot-data-fetcher")

# ECS Configuration (Legacy)
ECS_CLUSTER_NAME = os.getenv("ECS_CLUSTER_NAME", "trading-bot-cluster")
ECS_SERVICE_NAME = os.getenv("ECS_SERVICE_NAME", "trading-bot-strategy")
ECS_TASK_DEFINITION = os.getenv("ECS_TASK_DEFINITION", "trading-bot-strategy-task")

# Trading Configuration - Autonomous Mode
# Note: DEFAULT_SYMBOLS is deprecated in favor of autonomous selection
AUTONOMOUS_SELECTION = os.getenv("AUTONOMOUS_SELECTION", "true").lower() == "true"
MAX_POSITIONS = int(os.getenv("MAX_POSITIONS", "15"))
MIN_MARKET_CAP = float(os.getenv("MIN_MARKET_CAP", "1e9"))  # $1B default
MIN_VOLUME = int(os.getenv("MIN_VOLUME", "500000"))  # 500K shares
TRADING_ENABLED = os.getenv("TRADING_ENABLED", "false").lower() == "true"
PAPER_TRADING = os.getenv("PAPER_TRADING", "true").lower() == "true"

# Legacy fallback symbols (only used if autonomous selection fails)
FALLBACK_SYMBOLS = os.getenv("FALLBACK_SYMBOLS", "AAPL,MSFT,GOOGL").split(",")

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
        "use_mock_data": USE_MOCK_DATA,
        "api_keys": {
            "yahoo": YAHOO_API_KEY,
            "alpha_vantage": ALPHA_VANTAGE_API_KEY
        },
        # Legacy AWS configuration (for backward compatibility)
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
                "data_bucket": S3_BUCKET_DATA,
                "logs_prefix": S3_PREFIX_LOGS,
                "data_prefix": S3_PREFIX_DATA,
                "lambda_prefix": S3_PREFIX_LAMBDA
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
            "autonomous_selection": AUTONOMOUS_SELECTION,
            "max_positions": MAX_POSITIONS,
            "min_market_cap": MIN_MARKET_CAP,
            "min_volume": MIN_VOLUME,
            "trading_enabled": TRADING_ENABLED,
            "paper_trading": PAPER_TRADING,
            "default_symbols": FALLBACK_SYMBOLS,  # For API compatibility
            "fallback_symbols": FALLBACK_SYMBOLS
        },
        "logging": {
            "level": LOG_LEVEL,
            "format": LOG_FORMAT
        }
    }