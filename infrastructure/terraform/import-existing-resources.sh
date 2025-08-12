#!/bin/bash

# Script to import existing AWS resources into Terraform state
# This helps resolve "resource already exists" errors

set -e

PROJECT_NAME="${PROJECT_NAME:-cloud-trading-bot}"
AWS_REGION="${AWS_REGION:-us-west-2}"

echo "🔄 Importing existing AWS resources into Terraform state"
echo "Project: $PROJECT_NAME"
echo "Region: $AWS_REGION"
echo ""

# Function to check if resource exists in state
resource_in_state() {
    terraform state show "$1" >/dev/null 2>&1
}

# Function to import resource if it doesn't exist in state
import_if_missing() {
    local terraform_resource="$1"
    local aws_resource_id="$2"
    local resource_description="$3"
    
    if ! resource_in_state "$terraform_resource"; then
        echo "⚠️  Attempting to import $resource_description..."
        if terraform import "$terraform_resource" "$aws_resource_id" 2>/dev/null; then
            echo "✅ Successfully imported $resource_description"
        else
            echo "ℹ️  Resource $resource_description not found or already managed"
        fi
    else
        echo "✅ $resource_description already in state"
    fi
}

# Check if we're in the terraform directory
if [ ! -f "main.tf" ]; then
    echo "❌ Please run this script from the infrastructure/terraform directory"
    exit 1
fi

echo "📋 Checking and importing existing resources..."
echo ""

# Import IAM Roles
echo "🔐 IAM Roles:"
import_if_missing "aws_iam_role.lambda_role" "$PROJECT_NAME-lambda-role" "Lambda IAM Role"
import_if_missing "aws_iam_role.ecs_task_role" "$PROJECT_NAME-ecs-task-role" "ECS Task IAM Role"
import_if_missing "aws_iam_role.ecs_execution_role" "$PROJECT_NAME-ecs-execution-role" "ECS Execution IAM Role"

# Import S3 buckets
import_if_missing "aws_s3_bucket.lambda_deployment" "cloud-trading-bot-lambda-deployment-m6x4p8e" "Lambda Deployment S3 Bucket"
import_if_missing "aws_s3_bucket.trading_bot_logs" "cloud-trading-bot-lambda-deployment-m6x4p8e" "Trading Bot Logs S3 Bucket"

# Import IAM Role Policies
echo ""
echo "📝 IAM Role Policies:"
import_if_missing "aws_iam_role_policy.lambda_policy" "$PROJECT_NAME-lambda-role:$PROJECT_NAME-lambda-policy" "Lambda IAM Policy"
import_if_missing "aws_iam_role_policy.ecs_task_policy" "$PROJECT_NAME-ecs-task-role:$PROJECT_NAME-ecs-task-policy" "ECS Task IAM Policy"

# Import DynamoDB Tables
echo ""
echo "🗄️  DynamoDB Tables:"
import_if_missing "aws_dynamodb_table.config" "$PROJECT_NAME-config" "Config DynamoDB Table"
import_if_missing "aws_dynamodb_table.state" "$PROJECT_NAME-state" "State DynamoDB Table"
import_if_missing "aws_dynamodb_table.trades" "$PROJECT_NAME-trades" "Trades DynamoDB Table"

# Import ECR Repository
echo ""
echo "🐳 ECR Repository:"
import_if_missing "aws_ecr_repository.trading_bot_strategy" "$PROJECT_NAME-strategy" "ECR Repository"

# Import Secrets Manager Secret
echo ""
echo "🔐 Secrets Manager:"
import_if_missing "aws_secretsmanager_secret.trading_bot_secrets" "$PROJECT_NAME-secrets" "Secrets Manager Secret"

# Import CloudWatch Log Groups
echo ""
echo "📊 CloudWatch Log Groups:"
import_if_missing "aws_cloudwatch_log_group.lambda_logs" "/aws/lambda/$PROJECT_NAME-market-data-fetcher" "Lambda Log Group"
import_if_missing "aws_cloudwatch_log_group.ecs_logs" "/aws/ecs/$PROJECT_NAME-strategy" "ECS Log Group"

# Import ECS Resources
echo ""
echo "🏗️  ECS Resources:"
import_if_missing "aws_ecs_cluster.trading_bot_cluster" "$PROJECT_NAME-cluster" "ECS Cluster"

echo ""
echo "✅ Import process completed!"
echo ""
echo "📝 Next steps:"
echo "1. Run 'terraform plan' to verify the current state"
echo "2. If there are still resource conflicts, consider:"
echo "   - Manually deleting conflicting resources (if safe to do so)"
echo "   - Using data sources instead of creating new resources"
echo "   - Adjusting resource names to avoid conflicts"
echo ""
echo "⚠️  Note: Some resources like S3 buckets may have random suffixes"
echo "   and cannot be easily imported without knowing the exact names."
echo "   Check your AWS console for bucket names and import manually if needed:"
echo "   terraform import aws_s3_bucket.trading_bot_logs actual-bucket-name"
echo ""