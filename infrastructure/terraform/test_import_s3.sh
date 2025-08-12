#!/bin/bash

# Test script for import_s3.sh to verify functionality
# This script tests various scenarios to ensure the import script works correctly

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMPORT_SCRIPT="$SCRIPT_DIR/import_s3.sh"
TEST_LOG="test_import_s3.log"

# Colors for test output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

test_log() {
    local level="$1"
    shift
    local message="$*"
    
    case "$level" in
        "PASS")   echo -e "${GREEN}✅ PASS: $message${NC}" ;;
        "FAIL")   echo -e "${RED}❌ FAIL: $message${NC}" ;;
        "INFO")   echo -e "${BLUE}ℹ️  INFO: $message${NC}" ;;
        "WARN")   echo -e "${YELLOW}⚠️  WARN: $message${NC}" ;;
        *)        echo "$message" ;;
    esac
}

run_test() {
    local test_name="$1"
    shift
    local expected_exit_code="$1"
    shift
    local command=("$@")
    
    test_log "INFO" "Running test: $test_name"
    echo "Command: ${command[*]}"
    
    local actual_exit_code
    "${command[@]}" >/dev/null 2>&1 || actual_exit_code=$?
    actual_exit_code=${actual_exit_code:-0}
    
    if [ $actual_exit_code -eq $expected_exit_code ]; then
        test_log "PASS" "$test_name (exit code: $actual_exit_code)"
        return 0
    else
        test_log "FAIL" "$test_name (expected: $expected_exit_code, got: $actual_exit_code)"
        return 1
    fi
}

run_test_with_output() {
    local test_name="$1"
    shift
    local expected_exit_code="$1"
    shift
    local expected_output="$1"
    shift
    local command=("$@")
    
    test_log "INFO" "Running test: $test_name"
    echo "Command: ${command[*]}"
    
    local output
    local actual_exit_code
    output=$("${command[@]}" 2>&1) || actual_exit_code=$?
    actual_exit_code=${actual_exit_code:-0}
    
    local success=true
    
    if [ $actual_exit_code -ne $expected_exit_code ]; then
        test_log "FAIL" "$test_name (expected exit code: $expected_exit_code, got: $actual_exit_code)"
        success=false
    fi
    
    if [[ "$output" != *"$expected_output"* ]]; then
        test_log "FAIL" "$test_name (expected output to contain: '$expected_output')"
        echo "Actual output: $output"
        success=false
    fi
    
    if [ "$success" = true ]; then
        test_log "PASS" "$test_name"
        return 0
    else
        return 1
    fi
}

main() {
    echo "Starting import_s3.sh test suite"
    echo "================================"
    echo ""
    
    local total_tests=0
    local passed_tests=0
    
    # Test 1: Help functionality
    total_tests=$((total_tests + 1))
    if run_test_with_output "Help functionality" 0 "Usage:" "$IMPORT_SCRIPT" --help; then
        passed_tests=$((passed_tests + 1))
    fi
    echo ""
    
    # Test 2: Invalid option handling
    total_tests=$((total_tests + 1))
    if run_test_with_output "Invalid option handling" 1 "Unknown option" "$IMPORT_SCRIPT" --invalid-option; then
        passed_tests=$((passed_tests + 1))
    fi
    echo ""
    
    # Test 3: Wrong directory detection
    total_tests=$((total_tests + 1))
    if (cd /tmp && run_test_with_output "Wrong directory detection" 1 "No main.tf found" "$IMPORT_SCRIPT" --dry-run); then
        passed_tests=$((passed_tests + 1))
    fi
    echo ""
    
    # Test 4: Wrong main.tf content detection
    total_tests=$((total_tests + 1))
    if (cd /tmp && echo 'resource "aws_instance" "test" {}' > main.tf && run_test_with_output "Wrong main.tf content" 1 "does not contain the required S3 bucket resource" "$IMPORT_SCRIPT" --dry-run; rm -f main.tf); then
        passed_tests=$((passed_tests + 1))
    fi
    echo ""
    
    # Test 5: Custom parameters
    total_tests=$((total_tests + 1))
    if run_test_with_output "Custom parameters" 1 "Bucket Name:     test-bucket" "$IMPORT_SCRIPT" --bucket-name test-bucket --dry-run; then
        passed_tests=$((passed_tests + 1))
    fi
    echo ""
    
    # Test 6: Credential validation (should fail without AWS creds)
    total_tests=$((total_tests + 1))
    if (unset AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN && run_test_with_output "Credential validation" 1 "AWS credentials not configured" "$IMPORT_SCRIPT" --dry-run); then
        passed_tests=$((passed_tests + 1))
    fi
    echo ""
    
    # Summary
    echo "================================"
    echo "Test Results:"
    echo "  Total tests: $total_tests"
    echo "  Passed: $passed_tests"
    echo "  Failed: $((total_tests - passed_tests))"
    echo ""
    
    if [ $passed_tests -eq $total_tests ]; then
        test_log "PASS" "All tests passed! ✨"
        exit 0
    else
        test_log "FAIL" "Some tests failed"
        exit 1
    fi
}

main "$@"