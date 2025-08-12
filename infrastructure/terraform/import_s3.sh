#!/bin/bash

# Safe AWS Terraform S3 Import Script
# This script safely imports the S3 bucket into Terraform state with proper validation
# and error handling. It's idempotent and safe to run multiple times.

set -e

# Configuration
BUCKET_NAME="cloud-trading-bot-lambda-deployment-m6x4p8e"
TERRAFORM_RESOURCE="aws_s3_bucket.lambda_deployment"
AWS_REGION="${AWS_REGION:-us-west-2}"
LOG_FILE="import_s3.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Logging function with timestamps and colors
log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    # Log to file
    echo "[$timestamp] [$level] $message" >> "$LOG_FILE"
    
    # Display with colors
    case "$level" in
        "INFO")     echo -e "${BLUE}ℹ️  $message${NC}" ;;
        "WARN")     echo -e "${YELLOW}⚠️  $message${NC}" ;;
        "ERROR")    echo -e "${RED}❌ $message${NC}" ;;
        "SUCCESS")  echo -e "${GREEN}✅ $message${NC}" ;;
        "STEP")     echo -e "${CYAN}🔄 $message${NC}" ;;
        *)          echo "$message" ;;
    esac
}

# Display usage information
usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Safe AWS Terraform S3 Import Script

This script safely imports the S3 bucket '$BUCKET_NAME' into Terraform state
using the resource name '$TERRAFORM_RESOURCE'. It includes comprehensive
validation and is safe to run multiple times.

OPTIONS:
    -h, --help          Show this help message
    -r, --region        AWS region (default: us-west-2)
    -d, --dry-run       Show what would be done without making changes
    -v, --verbose       Enable verbose logging
    --bucket-name       Override bucket name (default: $BUCKET_NAME)
    --resource-name     Override Terraform resource name (default: $TERRAFORM_RESOURCE)

EXAMPLES:
    $0                  Import S3 bucket with default settings
    $0 --dry-run        Preview what would be imported
    $0 --verbose        Enable detailed logging
    $0 --region us-east-1  Use a different region

EOF
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                usage
                exit 0
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
            --bucket-name)
                BUCKET_NAME="$2"
                shift 2
                ;;
            --resource-name)
                TERRAFORM_RESOURCE="$2"
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

# Check if we're in the right directory
validate_directory() {
    log "STEP" "Validating directory structure..."
    
    if [ ! -f "main.tf" ]; then
        log "ERROR" "No main.tf found. Please run this script from the infrastructure/terraform directory"
        log "INFO" "Current directory: $(pwd)"
        exit 1
    fi
    
    # Check if this main.tf contains the S3 bucket resource we need to import
    if ! grep -q "resource.*aws_s3_bucket.*lambda_deployment" main.tf; then
        log "ERROR" "This main.tf does not contain the required S3 bucket resource 'aws_s3_bucket.lambda_deployment'"
        log "INFO" "Please run this script from the infrastructure/terraform directory"
        log "INFO" "Current directory: $(pwd)"
        exit 1
    fi
    
    log "SUCCESS" "Running from correct directory: $(pwd)"
}

# Validate required tools are installed
validate_tools() {
    log "STEP" "Validating required tools..."
    
    local errors=0
    
    if ! command -v aws &> /dev/null; then
        log "ERROR" "AWS CLI is not installed or not in PATH"
        log "INFO" "Install AWS CLI: https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html"
        errors=$((errors + 1))
    else
        local aws_version=$(aws --version 2>&1 | head -n 1)
        log "SUCCESS" "AWS CLI available: $aws_version"
    fi
    
    if ! command -v terraform &> /dev/null; then
        log "ERROR" "Terraform is not installed or not in PATH"
        log "INFO" "Install Terraform: https://learn.hashicorp.com/tutorials/terraform/install-cli"
        errors=$((errors + 1))
    else
        local tf_version=$(terraform version -json 2>/dev/null | grep -o '"terraform_version":"[^"]*"' | cut -d'"' -f4 2>/dev/null || terraform version | head -n 1)
        log "SUCCESS" "Terraform available: $tf_version"
    fi
    
    if [ $errors -gt 0 ]; then
        log "ERROR" "Missing required tools. Please install them and try again."
        exit 1
    fi
}

# Validate AWS credentials and permissions
validate_aws_credentials() {
    log "STEP" "Validating AWS credentials..."
    
    # Test AWS credentials
    if ! aws sts get-caller-identity --region "$AWS_REGION" >/dev/null 2>&1; then
        log "ERROR" "AWS credentials not configured or invalid"
        log "INFO" "Configure AWS credentials using one of these methods:"
        log "INFO" "  - aws configure"
        log "INFO" "  - Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables"
        log "INFO" "  - Use IAM roles if running on EC2"
        exit 1
    fi
    
    # Get and display caller identity
    local identity_json=$(aws sts get-caller-identity --region "$AWS_REGION" 2>/dev/null)
    local account_id=$(echo "$identity_json" | grep -o '"Account":"[^"]*"' | cut -d'"' -f4 2>/dev/null || echo "unknown")
    local user_arn=$(echo "$identity_json" | grep -o '"Arn":"[^"]*"' | cut -d'"' -f4 2>/dev/null || echo "unknown")
    
    log "SUCCESS" "AWS credentials valid"
    log "INFO" "AWS Account ID: $account_id"
    log "INFO" "AWS User/Role: $user_arn"
    log "INFO" "AWS Region: $AWS_REGION"
}

# Check if S3 bucket exists in AWS
check_bucket_exists() {
    log "STEP" "Checking if S3 bucket exists in AWS..."
    
    if aws s3api head-bucket --bucket "$BUCKET_NAME" --region "$AWS_REGION" >/dev/null 2>&1; then
        log "SUCCESS" "S3 bucket '$BUCKET_NAME' exists in AWS"
        
        # Get bucket region
        local bucket_region=$(aws s3api get-bucket-location --bucket "$BUCKET_NAME" --query 'LocationConstraint' --output text 2>/dev/null || echo "us-east-1")
        if [ "$bucket_region" = "None" ]; then
            bucket_region="us-east-1"
        fi
        log "INFO" "Bucket region: $bucket_region"
        
        if [ "$bucket_region" != "$AWS_REGION" ] && [ "$bucket_region" != "None" ]; then
            log "WARN" "Bucket region ($bucket_region) differs from specified region ($AWS_REGION)"
            log "INFO" "This is OK, but ensure you're using the correct region for other resources"
        fi
        
        return 0
    else
        log "ERROR" "S3 bucket '$BUCKET_NAME' does not exist in AWS"
        log "INFO" "Please create the bucket first or verify the bucket name"
        log "INFO" "You can create it with: aws s3 mb s3://$BUCKET_NAME --region $AWS_REGION"
        exit 1
    fi
}

# Initialize Terraform if needed
initialize_terraform() {
    log "STEP" "Checking Terraform initialization..."
    
    if [ ! -d ".terraform" ]; then
        log "INFO" "Terraform not initialized. Initializing..."
        if [ "$DRY_RUN" = "true" ]; then
            log "INFO" "[DRY RUN] Would run: terraform init"
        else
            if terraform init; then
                log "SUCCESS" "Terraform initialized successfully"
            else
                log "ERROR" "Failed to initialize Terraform"
                exit 1
            fi
        fi
    else
        log "SUCCESS" "Terraform already initialized"
    fi
}

# Check if resource is already in Terraform state
check_terraform_state() {
    log "STEP" "Checking if resource exists in Terraform state..."
    
    if terraform state show "$TERRAFORM_RESOURCE" >/dev/null 2>&1; then
        log "SUCCESS" "Resource '$TERRAFORM_RESOURCE' already exists in Terraform state"
        log "INFO" "No import needed - the resource is already managed by Terraform"
        return 0
    else
        log "INFO" "Resource '$TERRAFORM_RESOURCE' not found in Terraform state"
        log "INFO" "Import is needed"
        return 1
    fi
}

# Perform the actual import
import_s3_bucket() {
    log "STEP" "Importing S3 bucket into Terraform state..."
    
    if [ "$DRY_RUN" = "true" ]; then
        log "INFO" "[DRY RUN] Would run: terraform import $TERRAFORM_RESOURCE $BUCKET_NAME"
        log "INFO" "[DRY RUN] Import would complete successfully"
        return 0
    fi
    
    # Capture both stdout and stderr
    local import_output
    local import_exit_code
    
    if import_output=$(terraform import "$TERRAFORM_RESOURCE" "$BUCKET_NAME" 2>&1); then
        import_exit_code=0
    else
        import_exit_code=$?
    fi
    
    # Log the output
    if [ "$VERBOSE" = "true" ]; then
        log "INFO" "Terraform import output:"
        echo "$import_output" | while IFS= read -r line; do
            log "INFO" "  $line"
        done
    fi
    
    if [ $import_exit_code -eq 0 ]; then
        log "SUCCESS" "S3 bucket imported successfully into Terraform state"
        return 0
    else
        log "ERROR" "Failed to import S3 bucket"
        log "ERROR" "Terraform import output:"
        echo "$import_output" | while IFS= read -r line; do
            log "ERROR" "  $line"
        done
        exit 1
    fi
}

# Verify the import was successful
verify_import() {
    log "STEP" "Verifying import was successful..."
    
    if [ "$DRY_RUN" = "true" ]; then
        log "INFO" "[DRY RUN] Would verify that resource exists in Terraform state"
        return 0
    fi
    
    if terraform state show "$TERRAFORM_RESOURCE" >/dev/null 2>&1; then
        log "SUCCESS" "Import verification successful - resource is now in Terraform state"
        
        if [ "$VERBOSE" = "true" ]; then
            log "INFO" "Resource details:"
            terraform state show "$TERRAFORM_RESOURCE" | while IFS= read -r line; do
                log "INFO" "  $line"
            done
        fi
        
        return 0
    else
        log "ERROR" "Import verification failed - resource not found in Terraform state"
        exit 1
    fi
}

# Display next steps to the user
show_next_steps() {
    echo ""
    log "SUCCESS" "🎉 S3 bucket import completed successfully!"
    echo ""
    log "INFO" "📝 Next steps:"
    log "INFO" "1. Run 'terraform plan' to verify the current state matches your configuration"
    log "INFO" "2. If the plan shows no changes, your import was successful"
    log "INFO" "3. If the plan shows changes, you may need to update your Terraform configuration"
    log "INFO" "4. Run 'terraform apply' to apply any necessary changes"
    echo ""
    log "INFO" "🔍 Useful commands:"
    log "INFO" "  terraform state list                    # List all resources in state"
    log "INFO" "  terraform state show $TERRAFORM_RESOURCE  # Show imported resource details"
    log "INFO" "  terraform plan                          # Preview any changes needed"
    echo ""
    log "INFO" "📋 Import summary:"
    log "INFO" "  Resource: $TERRAFORM_RESOURCE"
    log "INFO" "  Bucket:   $BUCKET_NAME"
    log "INFO" "  Region:   $AWS_REGION"
    log "INFO" "  Log file: $LOG_FILE"
}

# Main execution function
main() {
    # Clear log file
    > "$LOG_FILE"
    
    echo ""
    log "INFO" "🚀 Starting Safe AWS Terraform S3 Import"
    log "INFO" "======================================"
    echo ""
    
    # Show configuration
    log "INFO" "Configuration:"
    log "INFO" "  Bucket Name:     $BUCKET_NAME"
    log "INFO" "  Resource Name:   $TERRAFORM_RESOURCE"
    log "INFO" "  AWS Region:      $AWS_REGION"
    log "INFO" "  Dry Run:         ${DRY_RUN:-false}"
    log "INFO" "  Verbose:         ${VERBOSE:-false}"
    log "INFO" "  Log File:        $LOG_FILE"
    echo ""
    
    # Run all validation and import steps
    validate_directory
    echo ""
    
    validate_tools
    echo ""
    
    validate_aws_credentials
    echo ""
    
    check_bucket_exists
    echo ""
    
    initialize_terraform
    echo ""
    
    # Check if already imported
    if check_terraform_state; then
        echo ""
        log "SUCCESS" "✨ Resource is already imported - nothing to do!"
        show_next_steps
        exit 0
    fi
    echo ""
    
    # Perform import
    import_s3_bucket
    echo ""
    
    # Verify import
    verify_import
    echo ""
    
    # Show next steps
    show_next_steps
}

# Parse arguments and run main function
parse_args "$@"

# Only run main if script is executed directly (not sourced)
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main
fi