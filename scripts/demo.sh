#!/bin/bash

# Demonstration of Workflow Troubleshooting Tools
# This script shows how to use the tools we've created

echo "🔧 GitHub Workflow Troubleshooting Tools Demo"
echo "============================================="
echo

echo "📁 Tools created:"
echo "  1. scripts/workflow_troubleshooter.py - Comprehensive Python tool"
echo "  2. scripts/check_workflow_logs.sh     - Quick bash tool"
echo "  3. scripts/README.md                  - Complete documentation"
echo

echo "🔍 Analysis of the failing commit 3a16d5b:"
echo "  - Workflow Run ID: 16938332353"
echo "  - Workflow: Deploy to Firebase Hosting on push to main"
echo "  - Error: npm ci package lock mismatch"
echo "  - Root Cause: package.json and package-lock.json out of sync"
echo

echo "🛠️ Issue Resolution Applied:"
echo "  ✅ Regenerated package-lock.json using npm install"
echo "  ✅ Fixed dependency version conflicts"
echo "  ✅ Created automated tools for future troubleshooting"
echo

echo "💡 Common Usage Examples:"
echo

echo "# Analyze specific commit"
echo "./scripts/check_workflow_logs.sh --commit 3a16d5b"
echo

echo "# Analyze specific workflow run"
echo "./scripts/check_workflow_logs.sh --run-id 16938332353"
echo

echo "# Show latest failed runs"
echo "./scripts/check_workflow_logs.sh --latest 5"
echo

echo "# Fix package lock issues"
echo "./scripts/check_workflow_logs.sh --fix-package-lock"
echo

echo "# Python detailed analysis"
echo "python scripts/workflow_troubleshooter.py --commit 3a16d5b8d3eb79212e074c7d570cc497db8a9dc7"
echo

echo "📋 Error Pattern Detection:"
echo "  ✅ npm package lock mismatch"
echo "  ✅ Missing dependencies"
echo "  ✅ Authentication failures"
echo "  ✅ Build failures"
echo "  ✅ Test failures"
echo

echo "🎯 Key Features:"
echo "  - Automated error analysis and suggestions"
echo "  - Log extraction and storage"
echo "  - Color-coded output for readability"
echo "  - Support for both quick bash and detailed Python analysis"
echo "  - Built-in fixes for common issues"
echo

echo "🔑 Authentication:"
echo "  Set GITHUB_TOKEN environment variable for better API access"
echo "  export GITHUB_TOKEN=your_github_token_here"
echo

echo "📖 For complete documentation, see: scripts/README.md"
echo

echo "✅ The package-lock.json issue has been fixed!"
echo "   Next push should trigger a successful workflow run."