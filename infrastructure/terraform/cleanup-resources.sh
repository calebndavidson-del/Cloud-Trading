#!/bin/bash

# Script to clean up resources that might conflict with Terraform deployment
# Use this when you want to start fresh or resolve "already exists" errors

set -e

PROJECT_NAME="${PROJECT_NAME:-cloud-trading-bot}"
AWS_REGION="${AWS_REGION:-us-west-2}"

echo "🧹 Cloud Trading Bot Resource Cleanup Script"
echo "Project: $PROJECT_NAME"
echo "Region: $AWS_REGION"
echo ""
echo "⚠️  WARNING: This script will DELETE AWS resources!"
echo "Make sure you understand what will be deleted before proceeding."
echo ""

# Function to confirm deletion
confirm_deletion() {
    local resource_type="$1"
    echo -n "Delete $resource_type? (y/N): "
    read -r response
    case "$response" in
        [yY][eE][sS]|[yY]) return 0 ;;
        *) return 1 ;;
    esac
}

# Function to delete resource if it exists
delete_if_exists() {
    local command="$1"
    local description="$2"
    
    echo "Attempting to delete $description..."
    if eval "$command" 2>/dev/null; then
        echo "✅ Deleted $description"
    else
        echo "ℹ️  $description not found or already deleted"
    fi
}

echo "📋 Available cleanup options:"
echo "1. IAM Roles and Policies"
echo "2. DynamoDB Tables"
echo "3. ECR Repository"
echo "4. Secrets Manager Secret"
echo "5. CloudWatch Log Groups"
echo "6. S3 Buckets (will list for manual deletion)"
echo "7. All of the above"
echo "0. Exit"
echo ""

read -p "Select option (0-7): " choice

case $choice in
    1|7)
        if confirm_deletion "IAM Roles and Policies"; then
            echo ""
            echo "🔐 Cleaning up IAM resources..."
            
            # Delete IAM role policies first
            delete_if_exists "aws iam delete-role-policy --role-name $PROJECT_NAME-lambda-role --policy-name $PROJECT_NAME-lambda-policy" "Lambda role policy"
            delete_if_exists "aws iam delete-role-policy --role-name $PROJECT_NAME-ecs-task-role --policy-name $PROJECT_NAME-ecs-task-policy" "ECS task role policy"
            
            # Detach managed policies
            delete_if_exists "aws iam detach-role-policy --role-name $PROJECT_NAME-ecs-execution-role --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy" "ECS execution role managed policy"
            
            # Delete IAM roles
            delete_if_exists "aws iam delete-role --role-name $PROJECT_NAME-lambda-role" "Lambda IAM role"
            delete_if_exists "aws iam delete-role --role-name $PROJECT_NAME-ecs-task-role" "ECS task IAM role"
            delete_if_exists "aws iam delete-role --role-name $PROJECT_NAME-ecs-execution-role" "ECS execution IAM role"
        fi
        ;;& # fall through
    
    2|7)
        if confirm_deletion "DynamoDB Tables"; then
            echo ""
            echo "🗄️  Cleaning up DynamoDB tables..."
            delete_if_exists "aws dynamodb delete-table --table-name $PROJECT_NAME-config" "Config DynamoDB table"
            delete_if_exists "aws dynamodb delete-table --table-name $PROJECT_NAME-state" "State DynamoDB table"
            delete_if_exists "aws dynamodb delete-table --table-name $PROJECT_NAME-trades" "Trades DynamoDB table"
        fi
        ;;& # fall through
    
    3|7)
        if confirm_deletion "ECR Repository"; then
            echo ""
            echo "🐳 Cleaning up ECR repository..."
            delete_if_exists "aws ecr delete-repository --repository-name $PROJECT_NAME-strategy --force" "ECR repository"
        fi
        ;;& # fall through
    
    4|7)
        if confirm_deletion "Secrets Manager Secret"; then
            echo ""
            echo "🔐 Cleaning up Secrets Manager secret..."
            delete_if_exists "aws secretsmanager delete-secret --secret-id $PROJECT_NAME-secrets --force-delete-without-recovery" "Secrets Manager secret"
        fi
        ;;& # fall through
    
    5|7)
        if confirm_deletion "CloudWatch Log Groups"; then
            echo ""
            echo "📊 Cleaning up CloudWatch log groups..."
            delete_if_exists "aws logs delete-log-group --log-group-name /aws/lambda/$PROJECT_NAME-market-data-fetcher" "Lambda log group"
            delete_if_exists "aws logs delete-log-group --log-group-name /aws/ecs/$PROJECT_NAME-strategy" "ECS log group"
        fi
        ;;& # fall through
    
    6|7)
        echo ""
        echo "🪣 S3 Buckets with project prefix:"
        echo "Note: S3 buckets have random suffixes and must be deleted manually"
        echo ""
        aws s3 ls | grep "$PROJECT_NAME" || echo "No buckets found with project prefix"
        echo ""
        echo "To delete S3 buckets:"
        echo "1. Empty the bucket: aws s3 rm s3://bucket-name --recursive"
        echo "2. Delete the bucket: aws s3 rb s3://bucket-name"
        ;;& # fall through
    
    0)
        echo "Exiting without making changes."
        exit 0
        ;;
    
    *)
        echo "Invalid option selected."
        exit 1
        ;;
esac

if [ "$choice" -eq 7 ]; then
    echo ""
    echo "🔄 Additional cleanup steps:"
    echo ""
    echo "Lambda Functions:"
    LAMBDA_FUNCTIONS=$(aws lambda list-functions --query "Functions[?starts_with(FunctionName, '$PROJECT_NAME')].FunctionName" --output text)
    if [ -n "$LAMBDA_FUNCTIONS" ]; then
        for func in $LAMBDA_FUNCTIONS; do
            delete_if_exists "aws lambda delete-function --function-name $func" "Lambda function $func"
        done
    else
        echo "ℹ️  No Lambda functions found with project prefix"
    fi
    
    echo ""
    echo "EventBridge Rules:"
    RULES=$(aws events list-rules --name-prefix "$PROJECT_NAME" --query "Rules[].Name" --output text)
    if [ -n "$RULES" ]; then
        for rule in $RULES; do
            # Remove targets first
            delete_if_exists "aws events remove-targets --rule $rule --ids 1" "EventBridge rule $rule targets"
            delete_if_exists "aws events delete-rule --name $rule" "EventBridge rule $rule"
        done
    else
        echo "ℹ️  No EventBridge rules found with project prefix"
    fi
    
    echo ""
    echo "ECS Resources:"
    # List and delete ECS services and clusters
    CLUSTERS=$(aws ecs list-clusters --query "clusterArns[?contains(@, '$PROJECT_NAME')]" --output text)
    if [ -n "$CLUSTERS" ]; then
        for cluster_arn in $CLUSTERS; do
            cluster_name=$(basename "$cluster_arn")
            
            # Get services in cluster
            SERVICES=$(aws ecs list-services --cluster "$cluster_name" --query "serviceArns" --output text)
            if [ -n "$SERVICES" ]; then
                for service_arn in $SERVICES; do
                    service_name=$(basename "$service_arn")
                    delete_if_exists "aws ecs update-service --cluster $cluster_name --service $service_name --desired-count 0" "ECS service $service_name (scaling down)"
                    sleep 10
                    delete_if_exists "aws ecs delete-service --cluster $cluster_name --service $service_name" "ECS service $service_name"
                done
            fi
            
            delete_if_exists "aws ecs delete-cluster --cluster $cluster_name" "ECS cluster $cluster_name"
        done
    else
        echo "ℹ️  No ECS clusters found with project prefix"
    fi
fi

echo ""
echo "✅ Cleanup completed!"
echo ""
echo "📝 Next steps:"
echo "1. Verify resources are deleted in AWS Console"
echo "2. Run 'terraform plan' to verify clean state"
echo "3. Deploy fresh infrastructure with './scripts/deploy.sh'"
echo ""
echo "💡 To prevent future conflicts:"
echo "- Set up remote state backend (see backend.tf)"
echo "- Use 'terraform import' for existing resources"
echo "- Enable resource randomization (already implemented)"
echo ""