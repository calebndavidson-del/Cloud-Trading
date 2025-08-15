#!/usr/bin/env python3
"""
Test script to verify region configuration in Cloud-Trading repository.
Validates that all region settings are correctly configured for us-west1.
"""

import os
import json
import sys
from pathlib import Path

def test_firebase_functions_region():
    """Test that Firebase Functions are configured for us-west1"""
    functions_file = Path("functions/main.py")
    if not functions_file.exists():
        return False, "functions/main.py not found"
    
    content = functions_file.read_text()
    if 'region="us-west1"' in content:
        return True, "Firebase Functions correctly configured for us-west1"
    elif 'region="us-central1"' in content:
        return False, "Firebase Functions configured for us-central1 (needs change)"
    else:
        return False, "No region configuration found in Firebase Functions"

def test_github_actions_region():
    """Test that GitHub Actions deployment uses us-west1"""
    workflow_file = Path(".github/workflows/deploy.yml")
    if not workflow_file.exists():
        return False, "GitHub Actions workflow not found"
    
    content = workflow_file.read_text()
    if 'REGION: us-west1' in content:
        return True, "GitHub Actions correctly configured for us-west1"
    elif 'REGION: us-central1' in content:
        return False, "GitHub Actions configured for us-central1 (needs change)"
    else:
        return False, "No region configuration found in GitHub Actions"

def test_documentation_consistency():
    """Test that documentation consistently references us-west1"""
    docs_to_check = [
        "README.md",
        "FIREBASE_DEPLOYMENT_GUIDE.md",
        "BACKTEST_INVESTIGATION_REPORT.md"
    ]
    
    issues = []
    for doc in docs_to_check:
        doc_path = Path(doc)
        if doc_path.exists():
            content = doc_path.read_text()
            if "us-central1" in content:
                issues.append(f"{doc} contains us-central1 references")
            elif "us-west1" not in content:
                # Only flag as issue if the doc should contain region references
                if any(term in content.lower() for term in ["firebase", "functions", "region", "google cloud"]):
                    issues.append(f"{doc} missing us-west1 references")
    
    if issues:
        return False, "; ".join(issues)
    return True, "Documentation consistently uses us-west1"

def test_no_central1_references():
    """Test that no files contain us-central1 references (excluding documentation)"""
    central1_files = []
    
    # Files to exclude from the check (documentation about regions)
    exclude_files = {
        "test_region_configuration.py",
        "REGION_CONFIGURATION_SUMMARY.md"
    }
    
    # Search common file types for us-central1
    for pattern in ["**/*.py", "**/*.js", "**/*.json", "**/*.yml", "**/*.yaml", "**/*.md", "**/*.tf"]:
        for file_path in Path(".").glob(pattern):
            if (file_path.is_file() and 
                not str(file_path).startswith(".git") and 
                file_path.name not in exclude_files):
                try:
                    content = file_path.read_text(encoding='utf-8', errors='ignore')
                    if "us-central1" in content:
                        central1_files.append(str(file_path))
                except:
                    pass  # Skip files that can't be read
    
    if central1_files:
        return False, f"Found us-central1 references in: {', '.join(central1_files)}"
    return True, "No us-central1 references found in configuration files"

def main():
    """Run all region configuration tests"""
    print("🔍 Testing Cloud-Trading region configuration...")
    print("=" * 50)
    
    tests = [
        ("Firebase Functions Region", test_firebase_functions_region),
        ("GitHub Actions Region", test_github_actions_region),
        ("Documentation Consistency", test_documentation_consistency),
        ("No us-central1 References", test_no_central1_references),
    ]
    
    all_passed = True
    
    for test_name, test_func in tests:
        try:
            passed, message = test_func()
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{status}: {test_name}")
            print(f"   → {message}")
            
            if not passed:
                all_passed = False
                
        except Exception as e:
            print(f"❌ ERROR: {test_name}")
            print(f"   → {str(e)}")
            all_passed = False
        
        print()
    
    print("=" * 50)
    if all_passed:
        print("🎉 All region configuration tests PASSED!")
        print("   The repository is correctly configured for us-west1")
        sys.exit(0)
    else:
        print("⚠️  Some region configuration tests FAILED!")
        print("   Please review the failed tests above")
        sys.exit(1)

if __name__ == "__main__":
    main()