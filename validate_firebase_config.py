#!/usr/bin/env python3
"""
Firebase Configuration Validator
Validates Firebase configuration and project setup
"""
import json
import os
import sys

def validate_firebase_config():
    """Validate Firebase configuration files"""
    print("🔧 Validating Firebase Configuration")
    print("=" * 50)
    
    config_files = [
        ("frontend/firebase.json", "Firebase Hosting Configuration"),
        ("functions/requirements.txt", "Functions Dependencies"),
        (".firebaserc", "Firebase Project Configuration"),
    ]
    
    issues = []
    
    for file_path, description in config_files:
        print(f"\n📄 Checking {description}...")
        if os.path.exists(file_path):
            print(f"   ✅ Found: {file_path}")
            
            if file_path.endswith('.json'):
                try:
                    with open(file_path, 'r') as f:
                        config = json.load(f)
                    print(f"   ✅ Valid JSON format")
                    
                    if 'firebase.json' in file_path:
                        # Check hosting rewrites
                        if 'hosting' in config and 'rewrites' in config['hosting']:
                            rewrites = config['hosting']['rewrites']
                            api_rewrite = next((r for r in rewrites if r.get('source') == '/api/**'), None)
                            if api_rewrite and api_rewrite.get('function') == 'api':
                                print("   ✅ API routing configured correctly")
                            else:
                                issues.append("API routing not configured for /api/** -> api function")
                        
                        # Check functions config
                        if 'functions' in config:
                            print("   ✅ Functions configuration present")
                        else:
                            issues.append("No functions configuration in firebase.json")
                    
                    elif '.firebaserc' in file_path:
                        if 'projects' in config and 'default' in config['projects']:
                            project_id = config['projects']['default']
                            if project_id == 'cloud-trading-bot-468900':
                                print(f"   ✅ Correct project ID: {project_id}")
                            else:
                                issues.append(f"Unexpected project ID: {project_id}")
                        
                except json.JSONDecodeError as e:
                    issues.append(f"Invalid JSON in {file_path}: {e}")
                    
            elif file_path.endswith('.txt'):
                try:
                    with open(file_path, 'r') as f:
                        content = f.read()
                    required_deps = ['firebase-functions', 'flask', 'flask-cors']
                    missing_deps = [dep for dep in required_deps if dep not in content]
                    if not missing_deps:
                        print("   ✅ Required dependencies present")
                    else:
                        issues.append(f"Missing dependencies: {missing_deps}")
                except Exception as e:
                    issues.append(f"Error reading {file_path}: {e}")
        else:
            issues.append(f"Missing file: {file_path}")
    
    # Check GitHub Actions workflow
    workflow_path = ".github/workflows/firebase-hosting.yml"
    print(f"\n🔄 Checking GitHub Actions Workflow...")
    if os.path.exists(workflow_path):
        print(f"   ✅ Found: {workflow_path}")
        try:
            with open(workflow_path, 'r') as f:
                workflow_content = f.read()
            
            checks = [
                ("firebase deploy", "Firebase deployment command"),
                ("python-version", "Python setup for Functions"),
                ("pip install -r requirements.txt", "Functions dependency installation"),
            ]
            
            for check, description in checks:
                if check in workflow_content:
                    print(f"   ✅ {description} configured")
                else:
                    issues.append(f"Missing in workflow: {description}")
                    
        except Exception as e:
            issues.append(f"Error reading workflow file: {e}")
    else:
        issues.append(f"Missing workflow file: {workflow_path}")
    
    print(f"\n" + "=" * 50)
    print("🔍 Configuration Validation Results")
    print("=" * 50)
    
    if not issues:
        print("🎉 All configuration files are valid!")
        print("Firebase deployment should work correctly.")
        return True
    else:
        print("⚠️  Configuration issues found:")
        for i, issue in enumerate(issues, 1):
            print(f"   {i}. {issue}")
        print("\nPlease fix these issues before deploying.")
        return False

def check_deployment_readiness():
    """Check if deployment is ready"""
    print("\n🚀 Deployment Readiness Check")
    print("=" * 50)
    
    # Check if functions can be imported
    try:
        sys.path.append('.')
        from functions.main import handle_request
        print("✅ Firebase Functions can be imported")
        functions_ready = True
    except Exception as e:
        print(f"❌ Firebase Functions import failed: {e}")
        functions_ready = False
    
    # Check if frontend build directory exists
    frontend_build = "frontend/build"
    if os.path.exists(frontend_build):
        print("✅ Frontend build directory exists")
        frontend_ready = True
    else:
        print("⚠️  Frontend build directory not found (run 'npm run build')")
        frontend_ready = False
    
    return functions_ready

if __name__ == "__main__":
    config_valid = validate_firebase_config()
    deployment_ready = check_deployment_readiness()
    
    if config_valid and deployment_ready:
        print("\n🎉 READY FOR DEPLOYMENT!")
        print("✅ Configuration is valid")
        print("✅ Functions are working")
        print("📤 You can now deploy to Firebase")
        sys.exit(0)
    else:
        print("\n⚠️  NOT READY FOR DEPLOYMENT")
        print("Please fix the issues above before deploying.")
        sys.exit(1)