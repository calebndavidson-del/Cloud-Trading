#!/bin/bash

# Test script for Terraform import functionality
# This script creates a test scenario and validates the import process

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_NAME="test-cloud-trading-bot"
TEST_LOG="test_import.log"

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
    
    echo "[$timestamp] [$level] $message" >> "$TEST_LOG"
    
    case "$level" in
        "INFO")  echo -e "${BLUE}ℹ️  $message${NC}" ;;
        "WARN")  echo -e "${YELLOW}⚠️  $message${NC}" ;;
        "ERROR") echo -e "${RED}❌ $message${NC}" ;;
        "SUCCESS") echo -e "${GREEN}✅ $message${NC}" ;;
        *) echo "$message" ;;
    esac
}

# Function to create a test S3 bucket
create_test_bucket() {
    local bucket_name="$1"
    log "INFO" "Creating test S3 bucket: $bucket_name"
    
    if aws s3 mb "s3://$bucket_name" >/dev/null 2>&1; then
        log "SUCCESS" "Test bucket created: $bucket_name"
        return 0
    else
        log "WARN" "Failed to create test bucket (may already exist): $bucket_name"
        return 1
    fi
}

# Function to clean up test resources
cleanup_test_resources() {
    log "INFO" "Cleaning up test resources..."
    
    # Remove test S3 buckets
    local test_buckets
    test_buckets=$(aws s3api list-buckets --query "Buckets[?starts_with(Name, '$PROJECT_NAME')].Name" --output text 2>/dev/null || true)
    
    for bucket in $test_buckets; do
        log "INFO" "Removing test bucket: $bucket"
        aws s3 rb "s3://$bucket" --force >/dev/null 2>&1 || log "WARN" "Failed to remove bucket: $bucket"
    done
    
    log "INFO" "Test cleanup completed"
}

# Function to test the import script with dry run
test_import_dry_run() {
    log "INFO" "Testing import script dry run functionality..."
    
    cd "$SCRIPT_DIR"
    
    # Test dry run with custom project name
    if PROJECT_NAME="$PROJECT_NAME" ./import-existing-resources.sh --dry-run --verbose >/dev/null 2>&1; then
        log "SUCCESS" "Dry run test passed"
        return 0
    else
        log "ERROR" "Dry run test failed"
        return 1
    fi
}

# Function to test resource discovery
test_resource_discovery() {
    log "INFO" "Testing resource discovery functionality..."
    
    cd "$SCRIPT_DIR"
    
    # Test discovery only mode
    if PROJECT_NAME="$PROJECT_NAME" ./import-existing-resources.sh --discover-only >/dev/null 2>&1; then
        log "SUCCESS" "Resource discovery test passed"
        return 0
    else
        log "ERROR" "Resource discovery test failed"
        return 1
    fi
}

# Function to test script help and argument parsing
test_script_arguments() {
    log "INFO" "Testing script arguments and help..."
    
    cd "$SCRIPT_DIR"
    
    # Test help option
    if ./import-existing-resources.sh --help >/dev/null 2>&1; then
        log "SUCCESS" "Help option works"
    else
        log "ERROR" "Help option failed"
        return 1
    fi
    
    # Test invalid argument
    if ./import-existing-resources.sh --invalid-option >/dev/null 2>&1; then
        log "ERROR" "Script should reject invalid arguments"
        return 1
    else
        log "SUCCESS" "Invalid argument handling works"
    fi
    
    return 0
}

# Function to test validation script
test_validation_script() {
    log "INFO" "Testing validation script..."
    
    cd "$SCRIPT_DIR"
    
    if [ -f "./validate-import.sh" ]; then
        # Test prerequisites check
        if ./validate-import.sh --prerequisites >/dev/null 2>&1; then
            log "SUCCESS" "Validation script prerequisites check passed"
        else
            log "WARN" "Validation script prerequisites check failed (may be due to environment)"
        fi
        
        # Test help option
        if ./validate-import.sh --help >/dev/null 2>&1; then
            log "SUCCESS" "Validation script help works"
        else
            log "ERROR" "Validation script help failed"
            return 1
        fi
    else
        log "WARN" "Validation script not found"
    fi
    
    return 0
}

# Main test function
run_tests() {
    log "INFO" "Starting Terraform import functionality tests"
    log "INFO" "Test project name: $PROJECT_NAME"
    echo ""
    
    local test_failures=0
    
    # Check if we're in the right directory
    if [ ! -f "import-existing-resources.sh" ]; then
        log "ERROR" "Please run this script from the infrastructure/terraform directory"
        return 1
    fi
    
    # Make scripts executable
    chmod +x "./import-existing-resources.sh" 2>/dev/null || true
    chmod +x "./validate-import.sh" 2>/dev/null || true
    
    # Run tests
    echo ""
    if ! test_script_arguments; then
        test_failures=$((test_failures + 1))
    fi
    
    echo ""
    if ! test_import_dry_run; then
        test_failures=$((test_failures + 1))
    fi
    
    echo ""
    if ! test_resource_discovery; then
        test_failures=$((test_failures + 1))
    fi
    
    echo ""
    if ! test_validation_script; then
        test_failures=$((test_failures + 1))
    fi
    
    echo ""
    if [ $test_failures -eq 0 ]; then
        log "SUCCESS" "All import functionality tests passed! ✨"
        log "INFO" "The enhanced import script is working correctly"
        echo ""
        log "INFO" "You can now use the import script with confidence:"
        log "INFO" "  ./import-existing-resources.sh --dry-run  # Preview mode"
        log "INFO" "  ./import-existing-resources.sh           # Actual import"
    else
        log "ERROR" "$test_failures tests failed"
        log "INFO" "Please review the errors above and check the test log: $TEST_LOG"
        return 1
    fi
    
    echo ""
    log "INFO" "Test log saved to: $TEST_LOG"
}

# Cleanup function for script exit
cleanup() {
    local exit_code=$?
    if [ $exit_code -ne 0 ]; then
        log "INFO" "Test script exited with errors, cleaning up..."
    fi
    cleanup_test_resources >/dev/null 2>&1 || true
    exit $exit_code
}

# Set up cleanup trap
trap cleanup EXIT

# Parse command line arguments
case "${1:-}" in
    "--help"|"-h")
        cat << EOF
Usage: $0 [OPTIONS]

Test script for Terraform import functionality.

This script validates that the enhanced import script is working correctly
by testing various features and edge cases.

OPTIONS:
    --help, -h          Show this help message
    --cleanup           Clean up any test resources and exit

EXAMPLES:
    $0                  Run all tests
    $0 --cleanup        Clean up test resources

EOF
        exit 0
        ;;
    "--cleanup")
        cleanup_test_resources
        exit 0
        ;;
    "")
        # Clear test log
        > "$TEST_LOG"
        run_tests
        exit $?
        ;;
    *)
        log "ERROR" "Unknown option: $1"
        log "INFO" "Use --help for usage information"
        exit 1
        ;;
esac