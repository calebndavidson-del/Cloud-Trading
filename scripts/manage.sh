#!/bin/bash

# AWS Trading Bot Management Script
# Utility script for managing the deployed trading bot

set -e

# Configuration
PROJECT_NAME="cloud-trading-bot"
AWS_REGION="${AWS_REGION:-us-west-2}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

usage() {
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  status      - Show status of all services"
    echo "  logs        - Show recent logs"
    echo "  start       - Start the trading bot services"
    echo "  stop        - Stop the trading bot services"
    echo "  restart     - Restart the trading bot services"
    echo "  update      - Update the strategy engine container"
    echo "  secrets     - Manage API secrets"
    echo "  cleanup     - Clean up old logs and data"
    echo "  destroy     - Destroy all AWS resources (DANGEROUS)"
    echo ""
}

check_aws_cli() {
    if ! command -v aws &> /dev/null; then
        echo -e "${RED}❌ AWS CLI is not installed${NC}"
        exit 1
    fi
}

get_terraform_output() {
    local output_name=$1
    cd infrastructure/terraform 2>/dev/null || {
        echo -e "${RED}❌ Terraform directory not found. Run deploy.sh first.${NC}"
        exit 1
    }
    terraform output -raw "$output_name" 2>/dev/null || echo ""
}

show_status() {
    echo -e "${BLUE}📊 Trading Bot Status${NC}"
    echo ""
    
    # Lambda function status
    echo -e "${YELLOW}🔧 Lambda Function:${NC}"
    LAMBDA_NAME=$(get_terraform_output lambda_function_name)
    if [ -n "$LAMBDA_NAME" ]; then
        aws lambda get-function --function-name "$LAMBDA_NAME" --query 'Configuration.[FunctionName,State,LastModified]' --output table
    else
        echo "  Not deployed"
    fi
    echo ""
    
    # ECS service status
    echo -e "${YELLOW}🐳 ECS Service:${NC}"
    ECS_CLUSTER=$(get_terraform_output ecs_cluster_name)
    ECS_SERVICE=$(get_terraform_output ecs_service_name)
    if [ -n "$ECS_CLUSTER" ] && [ -n "$ECS_SERVICE" ]; then
        aws ecs describe-services --cluster "$ECS_CLUSTER" --services "$ECS_SERVICE" --query 'services[0].[serviceName,status,runningCount,pendingCount,desiredCount]' --output table
    else
        echo "  Not deployed"
    fi
    echo ""
    
    # DynamoDB tables
    echo -e "${YELLOW}🗄️  DynamoDB Tables:${NC}"
    CONFIG_TABLE=$(get_terraform_output dynamodb_config_table)
    STATE_TABLE=$(get_terraform_output dynamodb_state_table)
    TRADES_TABLE=$(get_terraform_output dynamodb_trades_table)
    
    for table in "$CONFIG_TABLE" "$STATE_TABLE" "$TRADES_TABLE"; do
        if [ -n "$table" ]; then
            aws dynamodb describe-table --table-name "$table" --query 'Table.[TableName,TableStatus,ItemCount]' --output table 2>/dev/null || echo "  $table: Not accessible"
        fi
    done
    echo ""
    
    # S3 buckets
    echo -e "${YELLOW}🪣 S3 Buckets:${NC}"
    LOGS_BUCKET=$(get_terraform_output s3_logs_bucket)
    DATA_BUCKET=$(get_terraform_output s3_data_bucket)
    
    for bucket in "$LOGS_BUCKET" "$DATA_BUCKET"; do
        if [ -n "$bucket" ]; then
            if aws s3 ls "s3://$bucket" >/dev/null 2>&1; then
                echo "  ✅ $bucket"
            else
                echo "  ❌ $bucket: Not accessible"
            fi
        fi
    done
}

show_logs() {
    echo -e "${BLUE}📋 Recent Logs${NC}"
    echo ""
    
    LAMBDA_NAME=$(get_terraform_output lambda_function_name)
    ECS_CLUSTER=$(get_terraform_output ecs_cluster_name)
    
    echo -e "${YELLOW}Lambda Logs (last 50 lines):${NC}"
    if [ -n "$LAMBDA_NAME" ]; then
        aws logs tail "/aws/lambda/$LAMBDA_NAME" --since 1h | tail -50
    else
        echo "  Lambda not deployed"
    fi
    
    echo ""
    echo -e "${YELLOW}ECS Logs (last 50 lines):${NC}"
    if [ -n "$ECS_CLUSTER" ]; then
        aws logs tail "/aws/ecs/$PROJECT_NAME-strategy" --since 1h | tail -50
    else
        echo "  ECS not deployed"
    fi
}

start_services() {
    echo -e "${GREEN}🚀 Starting trading bot services${NC}"
    
    ECS_CLUSTER=$(get_terraform_output ecs_cluster_name)
    ECS_SERVICE=$(get_terraform_output ecs_service_name)
    
    if [ -n "$ECS_CLUSTER" ] && [ -n "$ECS_SERVICE" ]; then
        aws ecs update-service --cluster "$ECS_CLUSTER" --service "$ECS_SERVICE" --desired-count 1
        echo "✅ ECS service started"
    else
        echo "❌ ECS service not found"
    fi
}

stop_services() {
    echo -e "${YELLOW}⏹️  Stopping trading bot services${NC}"
    
    ECS_CLUSTER=$(get_terraform_output ecs_cluster_name)
    ECS_SERVICE=$(get_terraform_output ecs_service_name)
    
    if [ -n "$ECS_CLUSTER" ] && [ -n "$ECS_SERVICE" ]; then
        aws ecs update-service --cluster "$ECS_CLUSTER" --service "$ECS_SERVICE" --desired-count 0
        echo "✅ ECS service stopped"
    else
        echo "❌ ECS service not found"
    fi
}

restart_services() {
    echo -e "${BLUE}🔄 Restarting trading bot services${NC}"
    stop_services
    sleep 10
    start_services
}

update_container() {
    echo -e "${BLUE}📦 Updating strategy engine container${NC}"
    
    ECR_REPO=$(get_terraform_output ecr_repository_url)
    ECS_CLUSTER=$(get_terraform_output ecs_cluster_name)
    ECS_SERVICE=$(get_terraform_output ecs_service_name)
    
    if [ -n "$ECR_REPO" ]; then
        # Build and push new image
        echo "Building new container image..."
        aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin "$ECR_REPO"
        docker build -f infrastructure/docker/Dockerfile -t "$PROJECT_NAME-strategy" .
        docker tag "$PROJECT_NAME-strategy:latest" "$ECR_REPO:latest"
        docker push "$ECR_REPO:latest"
        
        # Force new deployment
        if [ -n "$ECS_CLUSTER" ] && [ -n "$ECS_SERVICE" ]; then
            aws ecs update-service --cluster "$ECS_CLUSTER" --service "$ECS_SERVICE" --force-new-deployment
            echo "✅ Container updated and service redeployed"
        fi
    else
        echo "❌ ECR repository not found"
    fi
}

manage_secrets() {
    SECRETS_ARN=$(get_terraform_output secrets_manager_arn)
    
    if [ -z "$SECRETS_ARN" ]; then
        echo "❌ Secrets Manager ARN not found"
        return 1
    fi
    
    echo -e "${BLUE}🔐 Managing API Secrets${NC}"
    echo ""
    echo "Current secrets structure:"
    aws secretsmanager get-secret-value --secret-id "$SECRETS_ARN" --query 'SecretString' --output text | jq .
    echo ""
    echo "To update secrets, use:"
    echo "aws secretsmanager update-secret --secret-id $SECRETS_ARN --secret-string '{\"yahoo_api_key\":\"your_key\"}'"
}

cleanup_old_data() {
    echo -e "${YELLOW}🧹 Cleaning up old logs and data${NC}"
    
    LOGS_BUCKET=$(get_terraform_output s3_logs_bucket)
    DATA_BUCKET=$(get_terraform_output s3_data_bucket)
    
    # Clean up S3 logs older than 30 days
    if [ -n "$LOGS_BUCKET" ]; then
        echo "Cleaning up logs older than 30 days in $LOGS_BUCKET..."
        aws s3api list-objects-v2 --bucket "$LOGS_BUCKET" --query "Contents[?LastModified<='$(date -d '30 days ago' --iso-8601)'].Key" --output text | \
        xargs -I {} aws s3 rm "s3://$LOGS_BUCKET/{}" 2>/dev/null || true
    fi
    
    # Clean up DynamoDB items with expired TTL (automatic, just report)
    STATE_TABLE=$(get_terraform_output dynamodb_state_table)
    if [ -n "$STATE_TABLE" ]; then
        ITEM_COUNT=$(aws dynamodb describe-table --table-name "$STATE_TABLE" --query 'Table.ItemCount' --output text)
        echo "State table $STATE_TABLE has $ITEM_COUNT items (TTL cleanup is automatic)"
    fi
    
    echo "✅ Cleanup completed"
}

destroy_infrastructure() {
    echo -e "${RED}⚠️  WARNING: This will destroy ALL AWS resources!${NC}"
    echo "This action cannot be undone."
    echo ""
    read -p "Type 'DESTROY' to confirm: " confirmation
    
    if [ "$confirmation" = "DESTROY" ]; then
        echo -e "${RED}🗑️  Destroying infrastructure...${NC}"
        cd infrastructure/terraform
        terraform destroy -auto-approve
        echo "✅ Infrastructure destroyed"
    else
        echo "❌ Destruction cancelled"
    fi
}

# Main script logic
check_aws_cli

case "${1:-}" in
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    start)
        start_services
        ;;
    stop)
        stop_services
        ;;
    restart)
        restart_services
        ;;
    update)
        update_container
        ;;
    secrets)
        manage_secrets
        ;;
    cleanup)
        cleanup_old_data
        ;;
    destroy)
        destroy_infrastructure
        ;;
    *)
        usage
        exit 1
        ;;
esac