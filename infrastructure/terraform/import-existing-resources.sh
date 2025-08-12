#!/bin/bash

# Enhanced script to import existing AWS resources into Terraform state
# This helps resolve "resource already exists" errors by dynamically discovering
# and importing existing resources before Terraform tries to create them.

set -e

# Configuration
PROJECT_NAME="${PROJECT_NAME:-cloud-trading-bot}"
AWS_REGION="${AWS_REGION:-us-west-2}"
DRY_RUN="${DRY_RUN:-false}"
VERBOSE="${VERBOSE:-false}"
LOG_FILE="${LOG_FILE:-import_resources.log}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] [$level] $message" >> "$LOG_FILE"
    case "$level" in
        "INFO")  echo -e "${BLUE}ℹ️  $message${NC}" ;;
        "WARN")  echo -e "${YELLOW}⚠️  $message${NC}" ;;
        "ERROR") echo -e "${RED}❌ $message${NC}" ;;
        "SUCCESS") echo -e "${GREEN}✅ $message${NC}" ;;
        *) echo "$message" ;;
    esac
}

resource_in_state() {
    terraform state show "$1" >/dev/null 2>&1
}

aws_resource_exists() {
    local resource_type="$1"
    local resource_id="$2"
    case "$resource_type" in
        "s3_bucket")
            aws s3api head-bucket --bucket "$resource_id" --region "$AWS_REGION" >/dev/null 2>&1
            ;;
        "iam_role")
            aws iam get-role --role-name "$resource_id" --region "$AWS_REGION" >/dev/null 2>&1
            ;;
        "dynamodb_table")
            aws dynamodb describe-table --table-name "$resource_id" --region "$AWS_REGION" >/dev/null 2>&1
            ;;
        "ecr_repository")
            aws ecr describe-repositories --repository-names "$resource_id" --region "$AWS_REGION" >/dev/null 2>&1
            ;;
        "cloudwatch_log_group")
            aws logs describe-log-groups --log-group-name-prefix "$resource_id" --region "$AWS_REGION" | jq -r '.logGroups[].logGroupName' | grep -q "^$resource_id$"
            ;;
        "secrets_manager_secret")
            aws secretsmanager describe-secret --secret-id "$resource_id" --region "$AWS_REGION" >/dev/null 2>&1
            ;;
        "lambda_function")
            aws lambda get-function --function-name "$resource_id" --region "$AWS_REGION" >/dev/null 2>&1
            ;;
        "ecs_cluster")
            aws ecs describe-clusters --clusters "$resource_id" --region "$AWS_REGION" | jq -r '.clusters[].status' | grep -q "ACTIVE"
            ;;
        *)
            log "WARN" "Unknown resource type: $resource_type"
            return 1
            ;;
    esac
}

import_if_missing() {
    local terraform_resource="$1"
    local aws_resource_id="$2"
    local resource_description="$3"
    local resource_type="$4"
    if resource_in_state "$terraform_resource"; then
        log "SUCCESS" "$resource_description already in Terraform state"
        return 0
    fi
    if ! aws_resource_exists "$resource_type" "$aws_resource_id"; then
        log "INFO" "$resource_description does not exist in AWS, skipping import"
        return 0
    fi
    log "INFO" "Attempting to import $resource_description (ID: $aws_resource_id)"
    if [ "$DRY_RUN" = "true" ]; then
        log "INFO" "[DRY RUN] Would import $terraform_resource with ID $aws_resource_id"
        return 0
    fi
    if terraform import "$terraform_resource" "$aws_resource_id" 2>/dev/null; then
        log "SUCCESS" "Successfully imported $resource_description"
        return 0
    else
        log "ERROR" "Failed to import $resource_description"
        return 1
    fi
}

discover_s3_buckets() {
    local prefix="$1"
    aws s3api list-buckets --query "Buckets[?starts_with(Name, '$prefix')].Name" --output text --region "$AWS_REGION" 2>/dev/null || true
}

discover_dynamodb_tables() {
    local prefix="$1"
    aws dynamodb list-tables --query "TableNames[?starts_with(@, '$prefix')]" --output text --region "$AWS_REGION" 2>/dev/null || true
}

discover_iam_roles() {
    local prefix="$1"
    aws iam list-roles --query "Roles[?starts_with(RoleName, '$prefix')].RoleName" --output text --region "$AWS_REGION" 2>/dev/null || true
}

discover_ecr_repositories() {
    local prefix="$1"
    aws ecr describe-repositories --query "repositories[?starts_with(repositoryName, '$prefix')].repositoryName" --output text --region "$AWS_REGION" 2>/dev/null || true
}

discover_lambda_functions() {
    local prefix="$1"
    aws lambda list-functions --query "Functions[?starts_with(FunctionName, '$prefix')].FunctionName" --output text --region "$AWS_REGION" 2>/dev/null || true
}

discover_cloudwatch_log_groups() {
    local prefix="$1"
    aws logs describe-log-groups --log-group-name-prefix "$prefix" --query "logGroups[].logGroupName" --output text --region "$AWS_REGION" 2>/dev/null || true
}

discover_ecs_clusters() {
    local prefix="$1"
    aws ecs list-clusters --query "clusterArns[?contains(@, '$prefix')]" --output text --region "$AWS_REGION" | sed 's|.*/||' 2>/dev/null || true
}

usage() {
    cat << EOF
Usage: $0 [OPTIONS]
Enhanced Terraform import script for Cloud Trading Bot infrastructure.
OPTIONS:
    -h, --help              Show this help message
    -p, --project-name      Project name prefix (default: cloud-trading-bot)
    -r, --region           AWS region (default: us-west-2)
    -d, --dry-run          Show what would be imported without actually importing
    -v, --verbose          Enable verbose logging
    -l, --log-file         Log file path (default: import_resources.log)
    --discover-only        Only discover resources, don't import
    --resource-type        Import only specific resource type (s3,iam,dynamodb,etc)
EOF
}

parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                usage
                exit 0
                ;;
            -p|--project-name)
                PROJECT_NAME="$2"
                shift 2
                ;;
            -r|--region)
                AWS_REGION="$2"
                shift 2
                ;;
            -d|--dry-run)
                DRY_RUN="true"
                shift
                ;;
            -v|--verbose)
                VERBOSE="true"
                shift
                ;;
            -l|--log-file)
                LOG_FILE="$2"
                shift 2
                ;;
            --discover-only)
                DISCOVER_ONLY="true"
                shift
                ;;
            --resource-type)
                RESOURCE_TYPE="$2"
                shift 2
                ;;
            *)
                log "ERROR" "Unknown option: $1"
                usage
                exit 1
                ;;
        esac
    done
}

main() {
    parse_args "$@"
    > "$LOG_FILE"
    log "INFO" "Enhanced Terraform Import Script for Cloud Trading Bot"
    log "INFO" "Project: $PROJECT_NAME"
    log "INFO" "Region: $AWS_REGION"
    log "INFO" "Dry Run: $DRY_RUN"
    log "INFO" "Log File: $LOG_FILE"
    echo ""
    if [ ! -f "main.tf" ]; then
        log "ERROR" "Please run this script from the infrastructure/terraform directory"
        exit 1
    fi
    if ! command -v aws &> /dev/null; then
        log "ERROR" "AWS CLI is not installed or not in PATH"
        exit 1
    fi
    if ! command -v terraform &> /dev/null; then
        log "ERROR" "Terraform is not installed or not in PATH"
        exit 1
    fi
    if ! command -v jq &> /dev/null; then
        log "WARN" "jq is not installed. Some features may not work properly."
    fi
    if ! aws sts get-caller-identity --region "$AWS_REGION" >/dev/null 2>&1; then
        log "ERROR" "AWS credentials not configured or invalid"
        exit 1
    fi

    log "INFO" "Discovering existing AWS resources..."
    echo ""

    if [ -z "$RESOURCE_TYPE" ] || [ "$RESOURCE_TYPE" = "s3" ]; then
        import_s3_resources
    fi
    if [ -z "$RESOURCE_TYPE" ] || [ "$RESOURCE_TYPE" = "iam" ]; then
        import_iam_resources
    fi
    if [ -z "$RESOURCE_TYPE" ] || [ "$RESOURCE_TYPE" = "dynamodb" ]; then
        import_dynamodb_resources
    fi
    if [ -z "$RESOURCE_TYPE" ] || [ "$RESOURCE_TYPE" = "ecr" ]; then
        import_ecr_resources
    fi
    if [ -z "$RESOURCE_TYPE" ] || [ "$RESOURCE_TYPE" = "lambda" ]; then
        import_lambda_resources
    fi
    if [ -z "$RESOURCE_TYPE" ] || [ "$RESOURCE_TYPE" = "cloudwatch" ]; then
        import_cloudwatch_resources
    fi
    if [ -z "$RESOURCE_TYPE" ] || [ "$RESOURCE_TYPE" = "secrets" ]; then
        import_secrets_resources
    fi
    if [ -z "$RESOURCE_TYPE" ] || [ "$RESOURCE_TYPE" = "ecs" ]; then
        import_ecs_resources
    fi

    echo ""
    if [ "$DRY_RUN" = "true" ]; then
        log "SUCCESS" "Dry run completed! Check log file: $LOG_FILE"
    elif [ "$DISCOVER_ONLY" = "true" ]; then
        log "SUCCESS" "Resource discovery completed! Check log file: $LOG_FILE"
    else
        log "SUCCESS" "Import process completed! Check log file: $LOG_FILE"
    fi

    echo ""
    log "INFO" "📝 Next steps:"
    log "INFO" "1. Run 'terraform plan' to verify the current state"
    log "INFO" "2. If there are still resource conflicts, consider:"
    log "INFO" "   - Running this script with --discover-only to see all available resources"
    log "INFO" "   - Manually importing specific resources using discovered names"
    log "INFO" "   - Using data sources instead of creating new resources"
    log "INFO" "   - Adjusting resource names in Terraform configuration"

    if [ "$VERBOSE" = "true" ]; then
        echo ""
        log "INFO" "📊 Summary of discovered resources:"
        echo "   Check $LOG_FILE for detailed discovery results"
    fi
}

import_s3_resources() {
    log "INFO" "🪣 Discovering S3 buckets..."
    local buckets
    buckets=$(discover_s3_buckets "$PROJECT_NAME")
    if [ -n "$buckets" ]; then
        log "INFO" "Found S3 buckets: $buckets"
        for bucket in $buckets; do
            if [ "$bucket" = "cloud-trading-bot-lambda-deployment-m6x4p8e" ]; then
                import_if_missing "aws_s3_bucket.lambda_deployment" "$bucket" "Lambda Deployment S3 Bucket (single bucket for all purposes)" "s3_bucket"
            else
                log "INFO" "Found unmatched S3 bucket: $bucket (manual import may be needed)"
            fi
        done
    else
        log "INFO" "No S3 buckets found with prefix: $PROJECT_NAME"
    fi
}

import_iam_resources() {
    log "INFO" "🔐 Discovering IAM roles..."
    local roles
    roles=$(discover_iam_roles "$PROJECT_NAME")
    if [ -n "$roles" ]; then
        log "INFO" "Found IAM roles: $roles"
        for role in $roles; do
            case "$role" in
                *"lambda-role"*)
                    import_if_missing "aws_iam_role.lambda_role" "$role" "Lambda IAM Role" "iam_role"
                    import_iam_role_policy "aws_iam_role_policy.lambda_policy" "$role" "${role/-role/-policy}" "Lambda IAM Policy"
                    ;;
                *"ecs-task-role"*)
                    import_if_missing "aws_iam_role.ecs_task_role" "$role" "ECS Task IAM Role" "iam_role"
                    import_iam_role_policy "aws_iam_role_policy.ecs_task_policy" "$role" "${role/-role/-policy}" "ECS Task IAM Policy"
                    ;;
                *"ecs-execution-role"*)
                    import_if_missing "aws_iam_role.ecs_execution_role" "$role" "ECS Execution IAM Role" "iam_role"
                    ;;
                *)
                    log "INFO" "Found unmatched IAM role: $role (manual import may be needed)"
                    ;;
            esac
        done
    else
        log "INFO" "No IAM roles found with prefix: $PROJECT_NAME"
    fi
}

import_dynamodb_resources() {
    log "INFO" "🗄️  Discovering DynamoDB tables..."
    local tables
    tables=$(discover_dynamodb_tables "$PROJECT_NAME")
    if [ -n "$tables" ]; then
        log "INFO" "Found DynamoDB tables: $tables"
        for table in $tables; do
            case "$table" in
                *"config"*)
                    import_if_missing "aws_dynamodb_table.config" "$table" "Config DynamoDB Table" "dynamodb_table"
                    ;;
                *"state"*)
                    import_if_missing "aws_dynamodb_table.state" "$table" "State DynamoDB Table" "dynamodb_table"
                    ;;
                *"trades"*)
                    import_if_missing "aws_dynamodb_table.trades" "$table" "Trades DynamoDB Table" "dynamodb_table"
                    ;;
                *)
                    log "INFO" "Found unmatched DynamoDB table: $table (manual import may be needed)"
                    ;;
            esac
        done
    else
        log "INFO" "No DynamoDB tables found with prefix: $PROJECT_NAME"
    fi
}

import_ecr_resources() {
    log "INFO" "🐳 Discovering ECR repositories..."
    local repos
    repos=$(discover_ecr_repositories "$PROJECT_NAME")
    if [ -n "$repos" ]; then
        log "INFO" "Found ECR repositories: $repos"
        for repo in $repos; do
            case "$repo" in
                *"strategy"*)
                    import_if_missing "aws_ecr_repository.trading_bot_strategy" "$repo" "ECR Repository" "ecr_repository"
                    ;;
                *)
                    log "INFO" "Found unmatched ECR repository: $repo (manual import may be needed)"
                    ;;
            esac
        done
    else
        log "INFO" "No ECR repositories found with prefix: $PROJECT_NAME"
    fi
}

import_lambda_resources() {
    log "INFO" "λ Discovering Lambda functions..."
    local functions
    functions=$(discover_lambda_functions "$PROJECT_NAME")
    if [ -n "$functions" ]; then
        log "INFO" "Found Lambda functions: $functions"
        for func in $functions; do
            case "$func" in
                *"market-data-fetcher"*)
                    import_if_missing "aws_lambda_function.market_data_fetcher" "$func" "Market Data Fetcher Lambda" "lambda_function"
                    ;;
                *)
                    log "INFO" "Found unmatched Lambda function: $func (manual import may be needed)"
                    ;;
            esac
        done
    else
        log "INFO" "No Lambda functions found with prefix: $PROJECT_NAME"
    fi
}

import_cloudwatch_resources() {
    log "INFO" "📊 Discovering CloudWatch log groups..."
    local log_groups
    log_groups=$(discover_cloudwatch_log_groups "/aws/lambda/$PROJECT_NAME")
    log_groups="$log_groups $(discover_cloudwatch_log_groups "/aws/ecs/$PROJECT_NAME")"
    if [ -n "$log_groups" ]; then
        log "INFO" "Found CloudWatch log groups: $log_groups"
        for log_group in $log_groups; do
            case "$log_group" in
                *"lambda"*"market-data-fetcher"*)
                    import_if_missing "aws_cloudwatch_log_group.lambda_logs" "$log_group" "Lambda Log Group" "cloudwatch_log_group"
                    ;;
                *"ecs"*"strategy"*)
                    import_if_missing "aws_cloudwatch_log_group.ecs_logs" "$log_group" "ECS Log Group" "cloudwatch_log_group"
                    ;;
                *)
                    log "INFO" "Found unmatched CloudWatch log group: $log_group (manual import may be needed)"
                    ;;
            esac
        done
    else
        log "INFO" "No CloudWatch log groups found with prefix: $PROJECT_NAME"
    fi
}

import_secrets_resources() {
    log "INFO" "🔐 Discovering Secrets Manager secrets..."
    local secrets
    secrets=$(aws secretsmanager list-secrets --query "SecretList[?contains(Name, '$PROJECT_NAME')].Name" --output text --region "$AWS_REGION" 2>/dev/null || true)
    if [ -n "$secrets" ]; then
        log "INFO" "Found secrets: $secrets"
        for secret in $secrets; do
            case "$secret" in
                *"secrets"*)
                    import_if_missing "aws_secretsmanager_secret.trading_bot_secrets" "$secret" "Secrets Manager Secret" "secrets_manager_secret"
                    ;;
                *)
                    log "INFO" "Found unmatched secret: $secret (manual import may be needed)"
                    ;;
            esac
        done
    else
        log "INFO" "No Secrets Manager secrets found with prefix: $PROJECT_NAME"
    fi
}

import_ecs_resources() {
    log "INFO" "🏗️  Discovering ECS clusters..."
    local clusters
    clusters=$(discover_ecs_clusters "$PROJECT_NAME")
    if [ -n "$clusters" ]; then
        log "INFO" "Found ECS clusters: $clusters"
        for cluster in $clusters; do
            case "$cluster" in
                *"cluster"*)
                    import_if_missing "aws_ecs_cluster.trading_bot_cluster" "$cluster" "ECS Cluster" "ecs_cluster"
                    ;;
                *)
                    log "INFO" "Found unmatched ECS cluster: $cluster (manual import may be needed)"
                    ;;
            esac
        done
    else
        log "INFO" "No ECS clusters found with prefix: $PROJECT_NAME"
    fi
}

import_iam_role_policy() {
    local terraform_resource="$1"
    local role_name="$2"
    local policy_name="$3"
    local resource_description="$4"
    if resource_in_state "$terraform_resource"; then
        log "SUCCESS" "$resource_description already in Terraform state"
        return 0
    fi
    if ! aws_resource_exists "iam_role" "$role_name"; then
        log "INFO" "IAM role $role_name does not exist, skipping policy import"
        return 0
    fi
    if ! aws iam get-role-policy --role-name "$role_name" --policy-name "$policy_name" --region "$AWS_REGION" >/dev/null 2>&1; then
        log "INFO" "IAM role policy $policy_name not found on role $role_name, skipping import"
        return 0
    fi
    local compound_id="$role_name:$policy_name"
    log "INFO" "Attempting to import $resource_description (ID: $compound_id)"
    if [ "$DRY_RUN" = "true" ]; then
        log "INFO" "[DRY RUN] Would import $terraform_resource with ID $compound_id"
        return 0
    fi
    if terraform import "$terraform_resource" "$compound_id" 2>/dev/null; then
        log "SUCCESS" "Successfully imported $resource_description"
        return 0
    else
        log "ERROR" "Failed to import $resource_description"
        return 1
    fi
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
