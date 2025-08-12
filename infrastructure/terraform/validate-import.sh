#!/bin/bash

# Validation script for Terraform import functionality
# This script helps test and validate the import process

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_NAME="${PROJECT_NAME:-cloud-trading-bot}"
AWS_REGION="${AWS_REGION:-us-west-2}"

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
    
    case "$level" in
        "INFO")  echo -e "${BLUE}ℹ️  $message${NC}" ;;
        "WARN")  echo -e "${YELLOW}⚠️  $message${NC}" ;;
        "ERROR") echo -e "${RED}❌ $message${NC}" ;;
        "SUCCESS") echo -e "${GREEN}✅ $message${NC}" ;;
        *) echo "$message" ;;
    esac
}

# Check prerequisites
check_prerequisites() {
    log "INFO" "Checking prerequisites for import validation..."
    
    local errors=0
    
    # Check if we're in the right directory
    if [ ! -f "main.tf" ]; then
        log "ERROR" "Please run this script from the infrastructure/terraform directory"
        errors=$((errors + 1))
    fi
    
    # Check required tools
    if ! command -v aws &> /dev/null; then
        log "ERROR" "AWS CLI is not installed or not in PATH"
        errors=$((errors + 1))
    fi
    
    if ! command -v terraform &> /dev/null; then
        log "ERROR" "Terraform is not installed or not in PATH"
        errors=$((errors + 1))
    fi
    
    if ! command -v jq &> /dev/null; then
        log "WARN" "jq is not installed. Install it for better validation features."
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity >/dev/null 2>&1; then
        log "ERROR" "AWS credentials not configured or invalid"
        errors=$((errors + 1))
    else
        local identity
        identity=$(aws sts get-caller-identity)
        local account_id
        account_id=$(echo "$identity" | jq -r '.Account' 2>/dev/null || echo "unknown")
        local user_arn
        user_arn=$(echo "$identity" | jq -r '.Arn' 2>/dev/null || echo "unknown")
        log "INFO" "AWS Account: $account_id"
        log "INFO" "AWS User/Role: $user_arn"
    fi
    
    # Check import script exists and is executable
    if [ ! -f "./import-existing-resources.sh" ]; then
        log "ERROR" "Import script not found: ./import-existing-resources.sh"
        errors=$((errors + 1))
    elif [ ! -x "./import-existing-resources.sh" ]; then
        log "WARN" "Import script is not executable, fixing..."
        chmod +x "./import-existing-resources.sh"
    fi
    
    if [ $errors -gt 0 ]; then
        log "ERROR" "Prerequisites check failed with $errors errors"
        return 1
    fi
    
    log "SUCCESS" "All prerequisites met"
    return 0
}

# Test resource discovery functions
test_discovery() {
    log "INFO" "Testing resource discovery..."
    
    # Test each resource type discovery
    log "INFO" "Discovering S3 buckets..."
    local s3_buckets
    s3_buckets=$(aws s3api list-buckets --query "Buckets[?starts_with(Name, '$PROJECT_NAME')].Name" --output text 2>/dev/null || true)
    if [ -n "$s3_buckets" ]; then
        log "SUCCESS" "Found S3 buckets: $s3_buckets"
    else
        log "INFO" "No S3 buckets found with prefix: $PROJECT_NAME"
    fi
    
    log "INFO" "Discovering IAM roles..."
    local iam_roles
    iam_roles=$(aws iam list-roles --query "Roles[?starts_with(RoleName, '$PROJECT_NAME')].RoleName" --output text 2>/dev/null || true)
    if [ -n "$iam_roles" ]; then
        log "SUCCESS" "Found IAM roles: $iam_roles"
    else
        log "INFO" "No IAM roles found with prefix: $PROJECT_NAME"
    fi
    
    log "INFO" "Discovering DynamoDB tables..."
    local dynamodb_tables
    dynamodb_tables=$(aws dynamodb list-tables --query "TableNames[?starts_with(@, '$PROJECT_NAME')]" --output text 2>/dev/null || true)
    if [ -n "$dynamodb_tables" ]; then
        log "SUCCESS" "Found DynamoDB tables: $dynamodb_tables"
    else
        log "INFO" "No DynamoDB tables found with prefix: $PROJECT_NAME"
    fi
    
    log "INFO" "Discovering Lambda functions..."
    local lambda_functions
    lambda_functions=$(aws lambda list-functions --query "Functions[?starts_with(FunctionName, '$PROJECT_NAME')].FunctionName" --output text 2>/dev/null || true)
    if [ -n "$lambda_functions" ]; then
        log "SUCCESS" "Found Lambda functions: $lambda_functions"
    else
        log "INFO" "No Lambda functions found with prefix: $PROJECT_NAME"
    fi
    
    log "SUCCESS" "Resource discovery test completed"
}

# Test import script dry run
test_dry_run() {
    log "INFO" "Testing import script in dry run mode..."
    
    if ! ./import-existing-resources.sh --dry-run --verbose; then
        log "ERROR" "Dry run test failed"
        return 1
    fi
    
    log "SUCCESS" "Dry run test completed successfully"
    
    # Check if log file was created
    if [ -f "import_resources.log" ]; then
        log "INFO" "Log file created with $(wc -l < import_resources.log) lines"
        
        # Check for any errors in the log
        if grep -q "ERROR" import_resources.log; then
            log "WARN" "Errors found in dry run log:"
            grep "ERROR" import_resources.log
        fi
    else
        log "WARN" "No log file created during dry run"
    fi
}

# Test discovery-only mode
test_discovery_only() {
    log "INFO" "Testing discovery-only mode..."
    
    if ! ./import-existing-resources.sh --discover-only --verbose; then
        log "ERROR" "Discovery-only test failed"
        return 1
    fi
    
    log "SUCCESS" "Discovery-only test completed successfully"
}

# Test specific resource type filtering
test_resource_filtering() {
    log "INFO" "Testing resource type filtering..."
    
    local resource_types=("s3" "iam" "dynamodb" "lambda" "ecr" "cloudwatch" "secrets" "ecs")
    
    for resource_type in "${resource_types[@]}"; do
        log "INFO" "Testing filter for resource type: $resource_type"
        if ! ./import-existing-resources.sh --dry-run --resource-type "$resource_type" >/dev/null 2>&1; then
            log "ERROR" "Failed to test resource type: $resource_type"
            return 1
        fi
    done
    
    log "SUCCESS" "Resource type filtering test completed"
}

# Test terraform state operations
test_terraform_state() {
    log "INFO" "Testing Terraform state operations..."
    
    # Initialize terraform if needed
    if [ ! -d ".terraform" ]; then
        log "INFO" "Initializing Terraform..."
        if ! terraform init >/dev/null 2>&1; then
            log "ERROR" "Failed to initialize Terraform"
            return 1
        fi
    fi
    
    # Test terraform commands used by import script
    log "INFO" "Testing terraform state list..."
    if ! terraform state list >/dev/null 2>&1; then
        log "WARN" "Terraform state list returned non-zero exit code (this may be normal for empty state)"
    fi
    
    log "INFO" "Testing terraform validate..."
    if ! terraform validate >/dev/null 2>&1; then
        log "ERROR" "Terraform configuration validation failed"
        return 1
    fi
    
    log "SUCCESS" "Terraform state operations test completed"
}

# Generate validation report
generate_report() {
    log "INFO" "Generating validation report..."
    
    local report_file="import_validation_report.txt"
    
    cat > "$report_file" << EOF
Terraform Import Validation Report
================================
Generated: $(date)
Project: $PROJECT_NAME
Region: $AWS_REGION

AWS Account Information:
$(aws sts get-caller-identity 2>/dev/null || echo "Unable to retrieve account info")

Terraform Version:
$(terraform version 2>/dev/null || echo "Terraform not available")

AWS CLI Version:
$(aws --version 2>/dev/null || echo "AWS CLI not available")

Available Tools:
- jq: $(command -v jq >/dev/null && echo "Available" || echo "Not available")
- terraform: $(command -v terraform >/dev/null && echo "Available" || echo "Not available")
- aws: $(command -v aws >/dev/null && echo "Available" || echo "Not available")

Discovered Resources:
=====================

S3 Buckets:
$(aws s3api list-buckets --query "Buckets[?starts_with(Name, '$PROJECT_NAME')].Name" --output text 2>/dev/null || echo "None found or error occurred")

IAM Roles:
$(aws iam list-roles --query "Roles[?starts_with(RoleName, '$PROJECT_NAME')].RoleName" --output text 2>/dev/null || echo "None found or error occurred")

DynamoDB Tables:
$(aws dynamodb list-tables --query "TableNames[?starts_with(@, '$PROJECT_NAME')]" --output text 2>/dev/null || echo "None found or error occurred")

Lambda Functions:
$(aws lambda list-functions --query "Functions[?starts_with(FunctionName, '$PROJECT_NAME')].FunctionName" --output text 2>/dev/null || echo "None found or error occurred")

ECR Repositories:
$(aws ecr describe-repositories --query "repositories[?starts_with(repositoryName, '$PROJECT_NAME')].repositoryName" --output text 2>/dev/null || echo "None found or error occurred")

Terraform State:
===============
$(terraform state list 2>/dev/null || echo "Unable to list state or state is empty")

EOF
    
    log "SUCCESS" "Validation report generated: $report_file"
}

# Main validation function
run_validation() {
    log "INFO" "Starting Terraform import validation..."
    echo ""
    
    local test_failures=0
    
    # Run all validation tests
    if ! check_prerequisites; then
        test_failures=$((test_failures + 1))
    fi
    
    echo ""
    if ! test_discovery; then
        test_failures=$((test_failures + 1))
    fi
    
    echo ""
    if ! test_dry_run; then
        test_failures=$((test_failures + 1))
    fi
    
    echo ""
    if ! test_discovery_only; then
        test_failures=$((test_failures + 1))
    fi
    
    echo ""
    if ! test_resource_filtering; then
        test_failures=$((test_failures + 1))
    fi
    
    echo ""
    if ! test_terraform_state; then
        test_failures=$((test_failures + 1))
    fi
    
    echo ""
    generate_report
    
    echo ""
    if [ $test_failures -eq 0 ]; then
        log "SUCCESS" "All validation tests passed! ✨"
        log "INFO" "You can now run the import script with confidence:"
        log "INFO" "  ./import-existing-resources.sh"
        echo ""
        log "INFO" "Or run a dry run first to see what would be imported:"
        log "INFO" "  ./import-existing-resources.sh --dry-run"
    else
        log "ERROR" "$test_failures validation tests failed"
        log "INFO" "Please review the errors above and fix them before running the import script"
        return 1
    fi
}

# Parse command line arguments
case "${1:-}" in
    "--help"|"-h")
        cat << EOF
Usage: $0 [OPTIONS]

Terraform Import Validation Script

This script validates that the import functionality is working correctly
and provides a report of what resources would be imported.

OPTIONS:
    --help, -h          Show this help message
    --report-only       Generate validation report only
    --prerequisites     Check prerequisites only
    --discovery         Test resource discovery only

EXAMPLES:
    $0                  Run full validation
    $0 --report-only    Generate report without running tests
    $0 --prerequisites  Check only prerequisites

EOF
        exit 0
        ;;
    "--report-only")
        generate_report
        exit 0
        ;;
    "--prerequisites")
        check_prerequisites
        exit $?
        ;;
    "--discovery")
        test_discovery
        exit $?
        ;;
    "")
        run_validation
        exit $?
        ;;
    *)
        log "ERROR" "Unknown option: $1"
        log "INFO" "Use --help for usage information"
        exit 1
        ;;
esac