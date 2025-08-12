# API Gateway Configuration for FastAPI deployment
# This allows the FastAPI server to be accessed via AWS API Gateway

# API Gateway REST API
resource "aws_api_gateway_rest_api" "trading_bot_api" {
  name        = "${var.project_name}-api-${random_string.suffix.result}"
  description = "Trading Bot API Gateway"

  endpoint_configuration {
    types = ["REGIONAL"]
  }

  tags = {
    Name = "Trading Bot API"
  }
}

# API Gateway Lambda Integration (for serverless FastAPI)
resource "aws_lambda_function" "api_server" {
  count            = var.deploy_api_gateway ? 1 : 0
  function_name    = "${var.project_name}-api-server-${random_string.suffix.result}"
  role            = aws_iam_role.lambda_role.arn
  handler         = "api_server.lambda_handler"
  runtime         = "python3.11"
  timeout         = 30
  memory_size     = 512

  s3_bucket = aws_s3_bucket.lambda_deployment.bucket
  s3_key    = var.lambda_s3_key

  environment {
    variables = {
      ENV                     = var.environment
      AWS_REGION             = var.aws_region
      DYNAMODB_CONFIG_TABLE  = aws_dynamodb_table.config.name
      DYNAMODB_STATE_TABLE   = aws_dynamodb_table.state.name
      DYNAMODB_TRADES_TABLE  = aws_dynamodb_table.trades.name
      S3_BUCKET_LOGS        = aws_s3_bucket.logs.bucket
      S3_BUCKET_DATA        = aws_s3_bucket.data.bucket
      SECRETS_MANAGER_ARN   = aws_secretsmanager_secret.trading_bot_secrets.arn
    }
  }

  depends_on = [
    aws_iam_role_policy_attachment.lambda_basic,
    aws_cloudwatch_log_group.lambda_api_logs,
  ]

  tags = {
    Name = "Trading Bot API Server"
  }
}

# CloudWatch Log Group for API Lambda
resource "aws_cloudwatch_log_group" "lambda_api_logs" {
  count             = var.deploy_api_gateway ? 1 : 0
  name              = "/aws/lambda/${var.project_name}-api-server-${random_string.suffix.result}"
  retention_in_days = 14

  tags = {
    Name = "Trading Bot API Lambda Logs"
  }
}

# API Gateway Lambda Permission
resource "aws_lambda_permission" "api_gateway_lambda" {
  count         = var.deploy_api_gateway ? 1 : 0
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.api_server[0].function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.trading_bot_api.execution_arn}/*/*"
}

# API Gateway Proxy Resource
resource "aws_api_gateway_resource" "proxy" {
  rest_api_id = aws_api_gateway_rest_api.trading_bot_api.id
  parent_id   = aws_api_gateway_rest_api.trading_bot_api.root_resource_id
  path_part   = "{proxy+}"
}

# API Gateway Proxy Method
resource "aws_api_gateway_method" "proxy" {
  rest_api_id   = aws_api_gateway_rest_api.trading_bot_api.id
  resource_id   = aws_api_gateway_resource.proxy.id
  http_method   = "ANY"
  authorization = "NONE"
}

# API Gateway Lambda Integration
resource "aws_api_gateway_integration" "lambda" {
  count = var.deploy_api_gateway ? 1 : 0
  
  rest_api_id = aws_api_gateway_rest_api.trading_bot_api.id
  resource_id = aws_api_gateway_method.proxy.resource_id
  http_method = aws_api_gateway_method.proxy.http_method

  integration_http_method = "POST"
  type                   = "AWS_PROXY"
  uri                    = aws_lambda_function.api_server[0].invoke_arn
}

# API Gateway Root Method (for health checks)
resource "aws_api_gateway_method" "proxy_root" {
  rest_api_id   = aws_api_gateway_rest_api.trading_bot_api.id
  resource_id   = aws_api_gateway_rest_api.trading_bot_api.root_resource_id
  http_method   = "ANY"
  authorization = "NONE"
}

# API Gateway Root Integration
resource "aws_api_gateway_integration" "lambda_root" {
  count = var.deploy_api_gateway ? 1 : 0
  
  rest_api_id = aws_api_gateway_rest_api.trading_bot_api.id
  resource_id = aws_api_gateway_method.proxy_root.resource_id
  http_method = aws_api_gateway_method.proxy_root.http_method

  integration_http_method = "POST"
  type                   = "AWS_PROXY"
  uri                    = aws_lambda_function.api_server[0].invoke_arn
}

# API Gateway Deployment
resource "aws_api_gateway_deployment" "trading_bot_api" {
  depends_on = [
    aws_api_gateway_integration.lambda,
    aws_api_gateway_integration.lambda_root,
  ]

  rest_api_id = aws_api_gateway_rest_api.trading_bot_api.id
  stage_name  = var.environment

  lifecycle {
    create_before_destroy = true
  }
}

# Custom Domain (optional)
resource "aws_api_gateway_domain_name" "trading_bot_api" {
  count           = var.api_domain_name != "" ? 1 : 0
  domain_name     = var.api_domain_name
  certificate_arn = var.api_certificate_arn

  tags = {
    Name = "Trading Bot API Domain"
  }
}

# Custom Domain Mapping
resource "aws_api_gateway_base_path_mapping" "trading_bot_api" {
  count       = var.api_domain_name != "" ? 1 : 0
  api_id      = aws_api_gateway_rest_api.trading_bot_api.id
  stage_name  = aws_api_gateway_deployment.trading_bot_api.stage_name
  domain_name = aws_api_gateway_domain_name.trading_bot_api[0].domain_name
}

# Variables for API Gateway
variable "deploy_api_gateway" {
  description = "Whether to deploy API Gateway for FastAPI server"
  type        = bool
  default     = true
}

variable "api_domain_name" {
  description = "Custom domain name for API Gateway (optional)"
  type        = string
  default     = ""
}

variable "api_certificate_arn" {
  description = "ACM certificate ARN for custom domain (required if api_domain_name is set)"
  type        = string
  default     = ""
}

# Outputs
output "api_gateway_url" {
  value = aws_api_gateway_deployment.trading_bot_api.invoke_url
  description = "API Gateway URL for the trading bot API"
}

output "api_gateway_id" {
  value = aws_api_gateway_rest_api.trading_bot_api.id
  description = "API Gateway ID"
}

output "api_lambda_function_name" {
  value = var.deploy_api_gateway ? aws_lambda_function.api_server[0].function_name : null
  description = "API Lambda function name"
}