# AWS Provider Configuration
terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "Cloud-Trading-Bot"
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

# Variables
variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-west-2"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "prod"
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "cloud-trading-bot"
}

variable "lambda_s3_key" {
  description = "S3 key for Lambda deployment package"
  type        = string
  default     = "lambda/lambda_deployment.zip"
}

# Data sources
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# Random suffix for unique naming
resource "random_string" "suffix" {
  length  = 8
  special = false
  upper   = false
}

# S3 Buckets
resource "aws_s3_bucket" "trading_bot_logs" {
  bucket = "cloud-trading-bot-lambda-deployment-m6x4p8e"
}

resource "aws_s3_bucket" "trading_bot_data" {
  bucket = "${var.project_name}-data-${random_string.suffix.result}"
}

# S3 bucket for Lambda deployment packages
resource "aws_s3_bucket" "lambda_deployment" {
  bucket = "cloud-trading-bot-lambda-deployment-m6x4p8e"
}

# Block public access for Lambda deployment bucket
resource "aws_s3_bucket_public_access_block" "lambda_deployment_pab" {
  bucket = aws_s3_bucket.lambda_deployment.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "trading_bot_logs_versioning" {
  bucket = aws_s3_bucket.trading_bot_logs.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_versioning" "trading_bot_data_versioning" {
  bucket = aws_s3_bucket.trading_bot_data.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "trading_bot_logs_lifecycle" {
  bucket = aws_s3_bucket.trading_bot_logs.id

  rule {
    id     = "delete_old_logs"
    status = "Enabled"

    filter {
      prefix = ""
    }

    expiration {
      days = 30
    }

    noncurrent_version_expiration {
      noncurrent_days = 7
    }
  }
}

# DynamoDB Tables
resource "aws_dynamodb_table" "config" {
  name         = "${var.project_name}-config-${random_string.suffix.result}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "id"

  attribute {
    name = "id"
    type = "S"
  }

  tags = {
    Name = "Trading Bot Configuration"
  }
}

resource "aws_dynamodb_table" "state" {
  name         = "${var.project_name}-state-${random_string.suffix.result}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "id"

  attribute {
    name = "id"
    type = "S"
  }

  ttl {
    attribute_name = "ttl"
    enabled        = true
  }

  tags = {
    Name = "Trading Bot State"
  }
}

resource "aws_dynamodb_table" "trades" {
  name         = "${var.project_name}-trades-${random_string.suffix.result}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "trade_id"

  attribute {
    name = "trade_id"
    type = "S"
  }

  attribute {
    name = "timestamp"
    type = "S"
  }

  global_secondary_index {
    name            = "timestamp-index"
    hash_key        = "timestamp"
    projection_type = "ALL"
  }

  tags = {
    Name = "Trading Bot Trades"
  }
}

# Secrets Manager
resource "aws_secretsmanager_secret" "trading_bot_secrets" {
  name                    = "${var.project_name}-secrets-${random_string.suffix.result}"
  description             = "API keys and secrets for trading bot"
  recovery_window_in_days = 7
}

resource "aws_secretsmanager_secret_version" "trading_bot_secrets_version" {
  secret_id = aws_secretsmanager_secret.trading_bot_secrets.id
  secret_string = jsonencode({
    yahoo_api_key      = ""
    alpha_vantage_key  = ""
    trading_api_key    = ""
    trading_api_secret = ""
  })
}

# IAM Role for Lambda
resource "aws_iam_role" "lambda_role" {
  name = "${var.project_name}-lambda-role-${random_string.suffix.result}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "lambda_policy" {
  name = "${var.project_name}-lambda-policy-${random_string.suffix.result}"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:GetItem",
          "dynamodb:UpdateItem",
          "dynamodb:Scan",
          "dynamodb:Query"
        ]
        Resource = [
          aws_dynamodb_table.config.arn,
          aws_dynamodb_table.state.arn,
          aws_dynamodb_table.trades.arn,
          "${aws_dynamodb_table.trades.arn}/index/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.trading_bot_logs.arn,
          "${aws_s3_bucket.trading_bot_logs.arn}/*",
          aws_s3_bucket.trading_bot_data.arn,
          "${aws_s3_bucket.trading_bot_data.arn}/*",
          aws_s3_bucket.lambda_deployment.arn,
          "${aws_s3_bucket.lambda_deployment.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = aws_secretsmanager_secret.trading_bot_secrets.arn
      }
    ]
  })
}

# CloudWatch Log Groups
resource "aws_cloudwatch_log_group" "lambda_logs" {
  name              = "/aws/lambda/${var.project_name}-market-data-fetcher-${random_string.suffix.result}"
  retention_in_days = 14
}

resource "aws_cloudwatch_log_group" "ecs_logs" {
  name              = "/aws/ecs/${var.project_name}-strategy-${random_string.suffix.result}"
  retention_in_days = 14
}

# Lambda Function
# Uses S3-based deployment for packages >70MB support
resource "aws_lambda_function" "market_data_fetcher" {
  # S3-based deployment configuration
  s3_bucket = aws_s3_bucket.lambda_deployment.bucket
  s3_key    = var.lambda_s3_key

  function_name = "${var.project_name}-market-data-fetcher-${random_string.suffix.result}"
  role          = aws_iam_role.lambda_role.arn
  handler       = "lambda_market_data.lambda_handler"
  runtime       = "python3.11"
  timeout       = 300
  memory_size   = 512

  # Track changes to the deployment package
  # Note: lambda_deployment.zip is created by the deployment script
  source_code_hash = filebase64sha256("lambda_deployment.zip")

  depends_on = [
    aws_iam_role_policy.lambda_policy,
    aws_cloudwatch_log_group.lambda_logs,
    aws_s3_bucket.lambda_deployment,
  ]

  environment {
    variables = {
      DYNAMODB_CONFIG_TABLE = aws_dynamodb_table.config.name
      DYNAMODB_STATE_TABLE  = aws_dynamodb_table.state.name
      DYNAMODB_TRADES_TABLE = aws_dynamodb_table.trades.name
      S3_BUCKET_LOGS        = aws_s3_bucket.trading_bot_logs.bucket
      S3_BUCKET_DATA        = aws_s3_bucket.trading_bot_data.bucket
      SECRETS_MANAGER_ARN   = aws_secretsmanager_secret.trading_bot_secrets.arn
      ENV                   = var.environment
      # Note: AWS_REGION is automatically provided by AWS Lambda runtime and cannot be set manually
    }
  }
}

# EventBridge Rule for periodic execution
resource "aws_cloudwatch_event_rule" "market_data_schedule" {
  name                = "${var.project_name}-market-data-schedule-${random_string.suffix.result}"
  description         = "Trigger market data fetching every 5 minutes during market hours"
  schedule_expression = "rate(5 minutes)"
}

resource "aws_cloudwatch_event_target" "lambda_target" {
  rule      = aws_cloudwatch_event_rule.market_data_schedule.name
  target_id = "MarketDataFetcherTarget"
  arn       = aws_lambda_function.market_data_fetcher.arn
}

resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.market_data_fetcher.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.market_data_schedule.arn
}

# Outputs
output "lambda_function_name" {
  value = aws_lambda_function.market_data_fetcher.function_name
}

output "lambda_deployment_bucket" {
  value       = aws_s3_bucket.lambda_deployment.bucket
  description = "S3 bucket for Lambda deployment packages"
}

output "lambda_s3_key" {
  value       = var.lambda_s3_key
  description = "S3 key for Lambda deployment package"
}

output "s3_logs_bucket" {
  value = aws_s3_bucket.trading_bot_logs.bucket
}

output "s3_data_bucket" {
  value = aws_s3_bucket.trading_bot_data.bucket
}

output "dynamodb_config_table" {
  value = aws_dynamodb_table.config.name
}

output "dynamodb_state_table" {
  value = aws_dynamodb_table.state.name
}

output "dynamodb_trades_table" {
  value = aws_dynamodb_table.trades.name
}

output "secrets_manager_arn" {
  value = aws_secretsmanager_secret.trading_bot_secrets.arn
}
