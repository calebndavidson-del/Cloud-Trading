# Workflow Troubleshooting Tools

This directory contains tools to help diagnose and fix GitHub Actions workflow failures.

## 🔧 Tools Available

### 1. Python Workflow Troubleshooter (`workflow_troubleshooter.py`)
A comprehensive Python script that provides detailed analysis of workflow failures.

**Features:**
- Analyze workflow runs for specific commits
- Get detailed job logs and failure analysis
- Automated suggestions for common issues
- Support for latest failed runs analysis

**Prerequisites:**
```bash
pip install requests
```

**Usage:**
```bash
# Analyze specific commit (the failing one from the issue)
python scripts/workflow_troubleshooter.py --commit 3a16d5b8d3eb79212e074c7d570cc497db8a9dc7

# Analyze specific workflow run
python scripts/workflow_troubleshooter.py --run-id 16938332353

# Analyze latest 5 failed runs
python scripts/workflow_troubleshooter.py --latest-failed --count 5

# Use with custom repository
python scripts/workflow_troubleshooter.py --repo owner/repo-name --commit abc123
```

### 2. Bash Workflow Log Checker (`check_workflow_logs.sh`)
A quick bash script for fast workflow analysis without Python dependencies.

**Prerequisites:**
- `curl` (usually pre-installed)
- `jq` (optional, for better JSON parsing)

**Usage:**
```bash
# Quick check of the failing commit
./scripts/check_workflow_logs.sh

# Check specific commit
./scripts/check_workflow_logs.sh --commit 3a16d5b

# Check specific workflow run
./scripts/check_workflow_logs.sh --run-id 16938332353

# Show latest failed runs
./scripts/check_workflow_logs.sh --latest 10

# Fix package-lock.json mismatch (for current issue)
./scripts/check_workflow_logs.sh --fix-package-lock

# Show help
./scripts/check_workflow_logs.sh --help
```

## 🔍 Current Issue Analysis

Based on the analysis of commit `3a16d5b8d3eb79212e074c7d570cc497db8a9dc7`, the workflow failed due to:

**Issue:** Package lock file mismatch in the frontend directory
```
npm ci can only install packages when your package.json and package-lock.json are in sync
Invalid: lock file's ajv@6.12.6 does not satisfy ajv@8.17.1
```

**Root Cause:** The `package.json` and `package-lock.json` files in the `frontend/` directory are out of sync.

**Solutions:**
1. **Quick fix using our script:**
   ```bash
   ./scripts/check_workflow_logs.sh --fix-package-lock
   ```

2. **Manual fix:**
   ```bash
   cd frontend
   rm -rf node_modules package-lock.json
   npm install
   git add package-lock.json
   git commit -m "Fix package-lock.json sync issue"
   ```

3. **Alternative (if you want to keep existing lockfile):**
   ```bash
   cd frontend
   npm install
   git add package-lock.json
   git commit -m "Update package-lock.json"
   ```

## 🔑 Authentication

For better API access and to avoid rate limits, set your GitHub token:

```bash
export GITHUB_TOKEN=your_github_token_here
```

Or create a `.env` file:
```
GITHUB_TOKEN=your_github_token_here
```

## 📊 Common Issues and Solutions

### 1. Package Lock File Mismatch
**Symptoms:** `npm ci` fails with sync error
**Solution:** Regenerate package-lock.json with `npm install`

### 2. Missing Dependencies
**Symptoms:** Missing packages from lock file
**Solution:** Update lockfile or check dependency versions

### 3. Authentication Errors
**Symptoms:** Unauthorized or permission denied errors
**Solution:** Check GitHub secrets and service account permissions

### 4. Build Failures
**Symptoms:** Compilation or build errors
**Solution:** Check source code syntax and dependencies

## 🚀 Integration with CI/CD

You can integrate these tools into your workflow for automatic failure analysis:

```yaml
- name: Analyze Workflow Failures
  if: failure()
  run: |
    python scripts/workflow_troubleshooter.py --run-id ${{ github.run_id }}
```

## 📝 Examples

### Example 1: Debug the Current Issue
```bash
# Using the bash script (quick)
./scripts/check_workflow_logs.sh --commit 3a16d5b

# Using the Python script (detailed)
python scripts/workflow_troubleshooter.py --commit 3a16d5b8d3eb79212e074c7d570cc497db8a9dc7
```

### Example 2: Monitor Failed Runs
```bash
# Get last 10 failed runs
./scripts/check_workflow_logs.sh --latest 10

# Analyze them with Python for detailed insights
python scripts/workflow_troubleshooter.py --latest-failed --count 10
```

### Example 3: Fix Current Package Issue
```bash
# Automated fix
./scripts/check_workflow_logs.sh --fix-package-lock

# Then commit the changes
git add frontend/package-lock.json
git commit -m "Fix: Regenerate package-lock.json to resolve workflow failure"
git push
```

## 📂 Output Files

The tools generate the following files:
- `logs_run_<run_id>_job_<job_id>.txt` - Full job logs for detailed analysis
- `package-lock.json.backup` - Backup of original lockfile (when using fix)

## 🤝 Contributing

To extend these tools:
1. Add new error patterns to the `error_patterns` dictionary
2. Implement additional analysis functions
3. Add support for more CI/CD platforms

## 📞 Support

If these tools don't help identify your issue:
1. Check the GitHub Actions logs directly in the UI
2. Run builds locally to reproduce issues
3. Review recent changes that might have caused the failure
4. Check for external service dependencies and API limits