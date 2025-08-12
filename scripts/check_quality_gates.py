#!/usr/bin/env python3
"""
Quality gate checks for CI/CD pipeline.
"""
import json
import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def check_coverage_threshold(threshold=70):
    """Check if coverage meets the threshold."""
    try:
        # Try to read coverage.xml
        coverage_files = ['coverage-unit.xml', 'coverage-integration.xml', 'coverage.xml']
        
        for coverage_file in coverage_files:
            if os.path.exists(coverage_file):
                tree = ET.parse(coverage_file)
                root = tree.getroot()
                
                # Find coverage percentage
                coverage_elem = root.find('.//coverage')
                if coverage_elem is not None:
                    line_rate = float(coverage_elem.get('line-rate', 0)) * 100
                    print(f"Coverage: {line_rate:.1f}%")
                    
                    if line_rate < threshold:
                        print(f"❌ Coverage {line_rate:.1f}% is below threshold {threshold}%")
                        return False
                    else:
                        print(f"✅ Coverage {line_rate:.1f}% meets threshold {threshold}%")
                        return True
        
        print("⚠️  No coverage data found")
        return False
        
    except Exception as e:
        print(f"Error checking coverage: {e}")
        return False


def check_test_results():
    """Check test results from JUnit XML files."""
    test_files = ['junit-unit.xml', 'junit-integration.xml', 'junit-e2e.xml']
    
    total_tests = 0
    total_failures = 0
    total_errors = 0
    
    for test_file in test_files:
        if os.path.exists(test_file):
            try:
                tree = ET.parse(test_file)
                root = tree.getroot()
                
                # Parse test results
                if root.tag == 'testsuites':
                    for testsuite in root.findall('testsuite'):
                        tests = int(testsuite.get('tests', 0))
                        failures = int(testsuite.get('failures', 0))
                        errors = int(testsuite.get('errors', 0))
                        
                        total_tests += tests
                        total_failures += failures
                        total_errors += errors
                        
                elif root.tag == 'testsuite':
                    total_tests += int(root.get('tests', 0))
                    total_failures += int(root.get('failures', 0))
                    total_errors += int(root.get('errors', 0))
                    
            except Exception as e:
                print(f"Error parsing {test_file}: {e}")
    
    if total_tests > 0:
        success_rate = ((total_tests - total_failures - total_errors) / total_tests) * 100
        print(f"Test Results: {total_tests} tests, {total_failures} failures, {total_errors} errors")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if total_failures > 0 or total_errors > 0:
            print("❌ Tests have failures or errors")
            return False
        else:
            print("✅ All tests passed")
            return True
    else:
        print("⚠️  No test results found")
        return False


def check_security_issues():
    """Check for critical security issues."""
    security_files = ['bandit-report.json', 'safety-report.json']
    
    critical_issues = 0
    
    # Check Bandit results
    if os.path.exists('bandit-report.json'):
        try:
            with open('bandit-report.json', 'r') as f:
                bandit_data = json.load(f)
                
            high_severity = len([issue for issue in bandit_data.get('results', []) 
                               if issue.get('issue_severity') == 'HIGH'])
            critical_issues += high_severity
            
            if high_severity > 0:
                print(f"❌ Found {high_severity} high severity security issues")
            else:
                print("✅ No high severity security issues found")
                
        except Exception as e:
            print(f"Error parsing bandit results: {e}")
    
    # Check Safety results
    if os.path.exists('safety-report.json'):
        try:
            with open('safety-report.json', 'r') as f:
                safety_data = json.load(f)
                
            vulnerabilities = len(safety_data)
            critical_issues += vulnerabilities
            
            if vulnerabilities > 0:
                print(f"❌ Found {vulnerabilities} dependency vulnerabilities")
            else:
                print("✅ No dependency vulnerabilities found")
                
        except Exception as e:
            print(f"Error parsing safety results: {e}")
    
    return critical_issues == 0


def main():
    """Run all quality gate checks."""
    print("🚀 Running Quality Gate Checks...")
    print("=" * 50)
    
    checks_passed = 0
    total_checks = 0
    
    # Check coverage
    print("\n📊 Checking Test Coverage...")
    total_checks += 1
    if check_coverage_threshold():
        checks_passed += 1
    
    # Check test results
    print("\n🧪 Checking Test Results...")
    total_checks += 1
    if check_test_results():
        checks_passed += 1
    
    # Check security
    print("\n🔒 Checking Security Issues...")
    total_checks += 1
    if check_security_issues():
        checks_passed += 1
    
    # Summary
    print("\n" + "=" * 50)
    print(f"Quality Gate Summary: {checks_passed}/{total_checks} checks passed")
    
    if checks_passed == total_checks:
        print("🎉 All quality gates passed!")
        sys.exit(0)
    else:
        print("❌ Some quality gates failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()