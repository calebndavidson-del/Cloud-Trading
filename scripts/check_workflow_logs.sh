#!/bin/bash

# GitHub Workflow Log Checker
# Quick bash script to fetch and analyze workflow failures

set -e

# Configuration
REPO_OWNER="calebndavidson-del"
REPO_NAME="Cloud-Trading"
GITHUB_API="https://api.github.com"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_color() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Function to check if required tools are available
check_dependencies() {
    if ! command -v curl &> /dev/null; then
        print_color $RED "Error: curl is required but not installed"
        exit 1
    fi
    
    if ! command -v jq &> /dev/null; then
        print_color $YELLOW "Warning: jq not found. JSON output will be raw"
        JQ_AVAILABLE=false
    else
        JQ_AVAILABLE=true
    fi
}

# Function to make GitHub API requests
github_api() {
    local endpoint=$1
    local headers=""
    
    if [[ -n "${GITHUB_TOKEN}" ]]; then
        headers="-H \"Authorization: token ${GITHUB_TOKEN}\""
    fi
    
    eval curl -s -H \"Accept: application/vnd.github.v3+json\" $headers \"${GITHUB_API}${endpoint}\"
}

# Function to get workflow runs for a commit
get_workflows_for_commit() {
    local commit_sha=$1
    print_color $BLUE "Fetching workflow runs for commit: $commit_sha"
    
    # Get all workflows first
    local workflows_response=$(github_api "/repos/${REPO_OWNER}/${REPO_NAME}/actions/workflows")
    
    if [[ $JQ_AVAILABLE == true ]]; then
        local workflow_ids=$(echo "$workflows_response" | jq -r '.workflows[].id')
        
        for workflow_id in $workflow_ids; do
            local runs_response=$(github_api "/repos/${REPO_OWNER}/${REPO_NAME}/actions/workflows/${workflow_id}/runs?head_sha=${commit_sha}")
            echo "$runs_response" | jq -r '.workflow_runs[] | select(.conclusion == "failure") | "\(.id) \(.name) \(.conclusion) \(.html_url)"'
        done
    else
        print_color $YELLOW "Install jq for better JSON parsing. Showing raw output:"
        echo "$workflows_response"
    fi
}

# Function to get failed job logs
get_failed_job_logs() {
    local run_id=$1
    print_color $BLUE "Getting failed job logs for run: $run_id"
    
    # Get jobs for the run
    local jobs_response=$(github_api "/repos/${REPO_OWNER}/${REPO_NAME}/actions/runs/${run_id}/jobs")
    
    if [[ $JQ_AVAILABLE == true ]]; then
        local failed_jobs=$(echo "$jobs_response" | jq -r '.jobs[] | select(.conclusion == "failure") | "\(.id) \(.name)"')
        
        while IFS=' ' read -r job_id job_name; do
            if [[ -n "$job_id" ]]; then
                print_color $RED "Failed Job: $job_name (ID: $job_id)"
                
                # Get logs for the failed job
                local log_url="${GITHUB_API}/repos/${REPO_OWNER}/${REPO_NAME}/actions/jobs/${job_id}/logs"
                local log_file="logs_${run_id}_${job_id}.txt"
                
                print_color $YELLOW "Downloading logs to: $log_file"
                
                if [[ -n "${GITHUB_TOKEN}" ]]; then
                    curl -s -L -H "Authorization: token ${GITHUB_TOKEN}" "$log_url" > "$log_file"
                else
                    curl -s -L "$log_url" > "$log_file"
                fi
                
                # Analyze the logs for common issues
                analyze_logs "$log_file"
            fi
        done <<< "$failed_jobs"
    else
        print_color $YELLOW "Install jq for automated log analysis. Raw jobs response:"
        echo "$jobs_response"
    fi
}

# Function to analyze logs and provide suggestions
analyze_logs() {
    local log_file=$1
    print_color $BLUE "Analyzing logs in: $log_file"
    
    # Check for common issues
    if grep -q "npm ci.*can only install packages when.*package\.json.*package-lock\.json.*are in sync" "$log_file"; then
        print_color $RED "🔍 ISSUE DETECTED: Package lock file mismatch"
        print_color $YELLOW "💡 SUGGESTED FIXES:"
        print_color $GREEN "   1. Run 'npm install' to update package-lock.json"
        print_color $GREEN "   2. Delete package-lock.json and node_modules, then run 'npm install'"
        print_color $GREEN "   3. Check if package.json was modified without updating package-lock.json"
        print_color $GREEN "   4. Use 'npm install' instead of 'npm ci' in development workflows"
    fi
    
    if grep -q "npm error Missing:.*from lock file" "$log_file"; then
        print_color $RED "🔍 ISSUE DETECTED: Missing packages in lock file"
        print_color $YELLOW "💡 SUGGESTED FIXES:"
        print_color $GREEN "   1. Update package-lock.json by running 'npm install'"
        print_color $GREEN "   2. Ensure all team members use the same npm/node versions"
    fi
    
    if grep -iq "authentication.*failed\|unauthorized\|permission.*denied" "$log_file"; then
        print_color $RED "🔍 ISSUE DETECTED: Authentication/Authorization error"
        print_color $YELLOW "💡 SUGGESTED FIXES:"
        print_color $GREEN "   1. Check GitHub secrets and tokens"
        print_color $GREEN "   2. Verify Firebase/cloud service credentials"
        print_color $GREEN "   3. Ensure service account has proper permissions"
    fi
    
    if grep -iq "build.*failed\|compilation.*error" "$log_file"; then
        print_color $RED "🔍 ISSUE DETECTED: Build failure"
        print_color $YELLOW "💡 SUGGESTED FIXES:"
        print_color $GREEN "   1. Check for syntax errors in source code"
        print_color $GREEN "   2. Verify all imports and dependencies"
        print_color $GREEN "   3. Run build locally to reproduce the issue"
    fi
    
    # Show error lines
    print_color $YELLOW "📋 Key error lines:"
    grep -i "error\|failed\|exception" "$log_file" | tail -10 | while read -r line; do
        print_color $RED "   $line"
    done
}

# Function to show latest failed runs
show_latest_failed() {
    local count=${1:-5}
    print_color $BLUE "Fetching last $count failed workflow runs"
    
    local runs_response=$(github_api "/repos/${REPO_OWNER}/${REPO_NAME}/actions/runs?status=completed&conclusion=failure&per_page=${count}")
    
    if [[ $JQ_AVAILABLE == true ]]; then
        echo "$runs_response" | jq -r '.workflow_runs[] | "\(.id) \(.name) \(.head_sha[0:8]) \(.created_at) \(.html_url)"' | \
        while read -r run_id name commit created url; do
            print_color $YELLOW "Run ID: $run_id"
            print_color $BLUE "  Name: $name"
            print_color $BLUE "  Commit: $commit"
            print_color $BLUE "  Created: $created"
            print_color $BLUE "  URL: $url"
            echo ""
        done
    else
        echo "$runs_response"
    fi
}

# Function to check specific workflow run
check_workflow_run() {
    local run_id=$1
    print_color $BLUE "Checking workflow run: $run_id"
    
    local run_response=$(github_api "/repos/${REPO_OWNER}/${REPO_NAME}/actions/runs/${run_id}")
    
    if [[ $JQ_AVAILABLE == true ]]; then
        local name=$(echo "$run_response" | jq -r '.name')
        local status=$(echo "$run_response" | jq -r '.status')
        local conclusion=$(echo "$run_response" | jq -r '.conclusion')
        local commit=$(echo "$run_response" | jq -r '.head_sha[0:8]')
        local url=$(echo "$run_response" | jq -r '.html_url')
        
        print_color $YELLOW "Workflow: $name"
        print_color $BLUE "Status: $status"
        print_color $BLUE "Conclusion: $conclusion"
        print_color $BLUE "Commit: $commit"
        print_color $BLUE "URL: $url"
        
        if [[ "$conclusion" == "failure" ]]; then
            get_failed_job_logs "$run_id"
        else
            print_color $GREEN "This workflow run did not fail"
        fi
    else
        echo "$run_response"
    fi
}

# Function to fix the current package lock issue
fix_package_lock() {
    print_color $BLUE "🔧 Attempting to fix package-lock.json mismatch..."
    
    if [[ -d "frontend" ]]; then
        cd frontend
        
        if [[ -f "package.json" ]]; then
            print_color $YELLOW "Backing up current package-lock.json..."
            if [[ -f "package-lock.json" ]]; then
                cp package-lock.json package-lock.json.backup
            fi
            
            print_color $YELLOW "Removing node_modules and package-lock.json..."
            rm -rf node_modules package-lock.json
            
            print_color $YELLOW "Running npm install to regenerate package-lock.json..."
            npm install
            
            print_color $GREEN "✅ Package lock file has been regenerated"
            print_color $YELLOW "Please commit the updated package-lock.json file"
        else
            print_color $RED "❌ No package.json found in frontend directory"
        fi
        
        cd ..
    else
        print_color $RED "❌ Frontend directory not found"
    fi
}

# Main function
main() {
    check_dependencies
    
    case "${1:-}" in
        --commit)
            if [[ -z "${2:-}" ]]; then
                print_color $RED "Error: Commit SHA required"
                exit 1
            fi
            get_workflows_for_commit "$2"
            ;;
        --run-id)
            if [[ -z "${2:-}" ]]; then
                print_color $RED "Error: Run ID required"
                exit 1
            fi
            check_workflow_run "$2"
            ;;
        --latest)
            show_latest_failed "${2:-5}"
            ;;
        --fix-package-lock)
            fix_package_lock
            ;;
        --help)
            echo "GitHub Workflow Log Checker"
            echo ""
            echo "Usage:"
            echo "  $0 --commit <sha>          Check workflows for specific commit"
            echo "  $0 --run-id <id>           Check specific workflow run"
            echo "  $0 --latest [count]        Show latest failed runs (default: 5)"
            echo "  $0 --fix-package-lock      Fix package-lock.json mismatch"
            echo "  $0 --help                  Show this help"
            echo ""
            echo "Environment variables:"
            echo "  GITHUB_TOKEN               GitHub personal access token (recommended)"
            echo ""
            echo "Examples:"
            echo "  $0 --commit 3a16d5b"
            echo "  $0 --run-id 16938332353"
            echo "  $0 --latest 10"
            ;;
        *)
            print_color $BLUE "🔍 Analyzing the failing commit: 3a16d5b8d3eb79212e074c7d570cc497db8a9dc7"
            get_workflows_for_commit "3a16d5b8d3eb79212e074c7d570cc497db8a9dc7"
            print_color $YELLOW "\nFor more options, run: $0 --help"
            ;;
    esac
}

# Run main function with all arguments
main "$@"