#!/usr/bin/env python3
"""
GitHub Workflow Troubleshooter

A comprehensive tool to check and retrieve logs from workflow runs to identify
the cause of failures. Provides automated analysis and suggestions for common issues.

Usage:
    python scripts/workflow_troubleshooter.py --commit <commit_sha>
    python scripts/workflow_troubleshooter.py --run-id <workflow_run_id>
    python scripts/workflow_troubleshooter.py --latest-failed
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime
from typing import Dict, List, Optional

try:
    import requests
except ImportError:
    print("Error: requests library not found. Install with: pip install requests")
    sys.exit(1)

class WorkflowTroubleshooter:
    def __init__(self, repo_owner: str, repo_name: str, github_token: Optional[str] = None):
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.github_token = github_token or os.environ.get('GITHUB_TOKEN')
        self.api_base = "https://api.github.com"
        
        self.headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'Workflow-Troubleshooter/1.0'
        }
        
        if self.github_token:
            self.headers['Authorization'] = f'token {self.github_token}'
    
    def get_workflows(self) -> List[Dict]:
        """Get all workflows in the repository."""
        url = f"{self.api_base}/repos/{self.repo_owner}/{self.repo_name}/actions/workflows"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json().get('workflows', [])
    
    def get_workflow_runs_for_commit(self, commit_sha: str) -> List[Dict]:
        """Get all workflow runs for a specific commit."""
        workflows = self.get_workflows()
        all_runs = []
        
        for workflow in workflows:
            url = f"{self.api_base}/repos/{self.repo_owner}/{self.repo_name}/actions/workflows/{workflow['id']}/runs"
            params = {'head_sha': commit_sha}
            response = requests.get(url, headers=self.headers, params=params)
            
            if response.status_code == 200:
                runs = response.json().get('workflow_runs', [])
                all_runs.extend(runs)
        
        return all_runs
    
    def get_workflow_run(self, run_id: int) -> Dict:
        """Get details of a specific workflow run."""
        url = f"{self.api_base}/repos/{self.repo_owner}/{self.repo_name}/actions/runs/{run_id}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def get_workflow_jobs(self, run_id: int) -> List[Dict]:
        """Get jobs for a workflow run."""
        url = f"{self.api_base}/repos/{self.repo_owner}/{self.repo_name}/actions/runs/{run_id}/jobs"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json().get('jobs', [])
    
    def get_job_logs(self, job_id: int) -> str:
        """Get logs for a specific job."""
        url = f"{self.api_base}/repos/{self.repo_owner}/{self.repo_name}/actions/jobs/{job_id}/logs"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code == 200:
            return response.text
        else:
            return f"Failed to retrieve logs: {response.status_code}"
    
    def get_latest_failed_runs(self, limit: int = 10) -> List[Dict]:
        """Get the latest failed workflow runs."""
        url = f"{self.api_base}/repos/{self.repo_owner}/{self.repo_name}/actions/runs"
        params = {'status': 'completed', 'conclusion': 'failure', 'per_page': limit}
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json().get('workflow_runs', [])
    
    def analyze_logs(self, logs: str) -> Dict:
        """Analyze logs and provide suggestions for common issues."""
        analysis = {
            'error_type': 'unknown',
            'error_message': '',
            'suggestions': [],
            'relevant_lines': []
        }
        
        lines = logs.split('\n')
        error_patterns = {
            'npm_dependency_mismatch': {
                'pattern': r'npm ci.*can only install packages when.*package\.json.*package-lock\.json.*are in sync',
                'suggestions': [
                    'Run `npm install` to update package-lock.json',
                    'Delete package-lock.json and node_modules, then run `npm install`',
                    'Check if package.json was modified without updating package-lock.json',
                    'Consider using `npm install` instead of `npm ci` in development workflows'
                ]
            },
            'npm_missing_package': {
                'pattern': r'npm error Missing:.*from lock file',
                'suggestions': [
                    'Update package-lock.json by running `npm install`',
                    'Check if dependencies were added without updating lockfile',
                    'Ensure all team members use the same npm/node versions'
                ]
            },
            'build_error': {
                'pattern': r'(BUILD FAILED|Error.*build|compilation.*error)',
                'suggestions': [
                    'Check for TypeScript/JavaScript syntax errors',
                    'Verify all imports and dependencies are correct',
                    'Run build locally to reproduce the issue',
                    'Check environment variables and configuration'
                ]
            },
            'test_failure': {
                'pattern': r'(test.*failed|Tests.*failed|FAIL.*test)',
                'suggestions': [
                    'Run tests locally to reproduce failures',
                    'Check if tests depend on external services',
                    'Verify test data and fixtures are available',
                    'Check for timing issues in async tests'
                ]
            },
            'auth_error': {
                'pattern': r'(authentication.*failed|unauthorized|permission.*denied)',
                'suggestions': [
                    'Check GitHub secrets and tokens',
                    'Verify Firebase/cloud service credentials',
                    'Ensure service account has proper permissions',
                    'Check if tokens have expired'
                ]
            }
        }
        
        for i, line in enumerate(lines):
            line_lower = line.lower()
            
            # Check for error patterns
            for error_type, config in error_patterns.items():
                if re.search(config['pattern'], line, re.IGNORECASE):
                    analysis['error_type'] = error_type
                    analysis['suggestions'].extend(config['suggestions'])
                    
                    # Capture context around the error
                    start = max(0, i - 2)
                    end = min(len(lines), i + 3)
                    analysis['relevant_lines'].extend(lines[start:end])
            
            # Capture explicit error messages
            if any(keyword in line_lower for keyword in ['error', 'failed', 'exception']):
                if len(line.strip()) > 0:
                    analysis['error_message'] = line.strip()
                    if line not in analysis['relevant_lines']:
                        analysis['relevant_lines'].append(line)
        
        # Remove duplicates from suggestions and relevant lines
        analysis['suggestions'] = list(dict.fromkeys(analysis['suggestions']))
        analysis['relevant_lines'] = list(dict.fromkeys(analysis['relevant_lines']))
        
        return analysis
    
    def display_run_summary(self, run: Dict):
        """Display a summary of a workflow run."""
        print(f"\n🔍 Workflow Run Summary")
        print(f"   ID: {run['id']}")
        print(f"   Name: {run['name']}")
        print(f"   Status: {run['status']}")
        print(f"   Conclusion: {run.get('conclusion', 'N/A')}")
        print(f"   Commit: {run['head_sha'][:8]}")
        print(f"   Branch: {run['head_branch']}")
        print(f"   Created: {run['created_at']}")
        print(f"   URL: {run['html_url']}")
    
    def display_analysis(self, analysis: Dict):
        """Display log analysis results."""
        print(f"\n📊 Log Analysis")
        print(f"   Error Type: {analysis['error_type']}")
        
        if analysis['error_message']:
            print(f"   Error Message: {analysis['error_message']}")
        
        if analysis['relevant_lines']:
            print(f"\n📋 Relevant Log Lines:")
            for line in analysis['relevant_lines'][-10:]:  # Show last 10 relevant lines
                print(f"   {line}")
        
        if analysis['suggestions']:
            print(f"\n💡 Suggested Solutions:")
            for i, suggestion in enumerate(analysis['suggestions'], 1):
                print(f"   {i}. {suggestion}")
    
    def troubleshoot_commit(self, commit_sha: str):
        """Troubleshoot all workflow runs for a specific commit."""
        print(f"🔎 Analyzing workflow runs for commit: {commit_sha}")
        
        runs = self.get_workflow_runs_for_commit(commit_sha)
        
        if not runs:
            print(f"❌ No workflow runs found for commit {commit_sha}")
            return
        
        failed_runs = [run for run in runs if run.get('conclusion') == 'failure']
        
        if not failed_runs:
            print(f"✅ All workflow runs passed for commit {commit_sha}")
            return
        
        print(f"⚠️  Found {len(failed_runs)} failed workflow run(s)")
        
        for run in failed_runs:
            self.display_run_summary(run)
            self.troubleshoot_run(run['id'])
    
    def troubleshoot_run(self, run_id: int):
        """Troubleshoot a specific workflow run."""
        print(f"\n🔧 Troubleshooting workflow run: {run_id}")
        
        try:
            run = self.get_workflow_run(run_id)
            jobs = self.get_workflow_jobs(run_id)
            
            failed_jobs = [job for job in jobs if job.get('conclusion') == 'failure']
            
            if not failed_jobs:
                print(f"ℹ️  No failed jobs found for run {run_id}")
                return
            
            for job in failed_jobs:
                print(f"\n❌ Failed Job: {job['name']} (ID: {job['id']})")
                print(f"   Started: {job.get('started_at', 'N/A')}")
                print(f"   Duration: {job.get('created_at', 'N/A')} - {job.get('completed_at', 'N/A')}")
                
                logs = self.get_job_logs(job['id'])
                analysis = self.analyze_logs(logs)
                self.display_analysis(analysis)
                
                # Optionally save full logs to file
                log_filename = f"logs_run_{run_id}_job_{job['id']}.txt"
                with open(log_filename, 'w') as f:
                    f.write(logs)
                print(f"\n💾 Full logs saved to: {log_filename}")
        
        except Exception as e:
            print(f"❌ Error troubleshooting run {run_id}: {e}")
    
    def troubleshoot_latest_failed(self, count: int = 5):
        """Troubleshoot the latest failed workflow runs."""
        print(f"🔎 Analyzing the last {count} failed workflow runs")
        
        failed_runs = self.get_latest_failed_runs(count)
        
        if not failed_runs:
            print("✅ No recent failed workflow runs found")
            return
        
        for run in failed_runs:
            self.display_run_summary(run)
            self.troubleshoot_run(run['id'])

def main():
    parser = argparse.ArgumentParser(description='GitHub Workflow Troubleshooter')
    parser.add_argument('--repo', default='calebndavidson-del/Cloud-Trading', 
                       help='Repository in owner/name format')
    parser.add_argument('--commit', help='Commit SHA to analyze')
    parser.add_argument('--run-id', type=int, help='Specific workflow run ID to analyze')
    parser.add_argument('--latest-failed', action='store_true', 
                       help='Analyze latest failed runs')
    parser.add_argument('--count', type=int, default=5, 
                       help='Number of latest failed runs to analyze')
    parser.add_argument('--token', help='GitHub token (or set GITHUB_TOKEN env var)')
    
    args = parser.parse_args()
    
    # Parse repository
    if '/' not in args.repo:
        print("❌ Repository must be in 'owner/name' format")
        sys.exit(1)
    
    owner, name = args.repo.split('/', 1)
    
    # Initialize troubleshooter
    troubleshooter = WorkflowTroubleshooter(owner, name, args.token)
    
    try:
        if args.commit:
            troubleshooter.troubleshoot_commit(args.commit)
        elif args.run_id:
            troubleshooter.troubleshoot_run(args.run_id)
        elif args.latest_failed:
            troubleshooter.troubleshoot_latest_failed(args.count)
        else:
            # Default: analyze the specific failing commit from the issue
            troubleshooter.troubleshoot_commit('3a16d5b8d3eb79212e074c7d570cc497db8a9dc7')
    
    except requests.exceptions.RequestException as e:
        print(f"❌ API request failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()