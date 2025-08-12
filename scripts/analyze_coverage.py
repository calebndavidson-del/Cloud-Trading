#!/usr/bin/env python3
"""
Analyze code coverage and suggest missing tests.
"""
import sys
import os
import ast
import subprocess
from pathlib import Path


def get_python_files(changed_files):
    """Get Python files from the list of changed files."""
    python_files = []
    with open(changed_files, 'r') as f:
        for line in f:
            file_path = line.strip()
            if file_path.endswith('.py') and not file_path.startswith('tests/'):
                python_files.append(file_path)
    return python_files


def analyze_functions_and_classes(file_path):
    """Analyze Python file to extract functions and classes."""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        tree = ast.parse(content, filename=file_path)
        
        functions = []
        classes = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if not node.name.startswith('_'):  # Skip private functions
                    functions.append(node.name)
            elif isinstance(node, ast.ClassDef):
                classes.append(node.name)
        
        return functions, classes
    except Exception as e:
        print(f"Error analyzing {file_path}: {e}", file=sys.stderr)
        return [], []


def check_existing_tests(module_path):
    """Check if tests exist for the given module."""
    test_file_patterns = [
        f"tests/unit/test_{os.path.basename(module_path)}",
        f"tests/unit/{os.path.dirname(module_path)}/test_{os.path.basename(module_path)}",
        f"tests/integration/test_{os.path.basename(module_path)}"
    ]
    
    for pattern in test_file_patterns:
        if os.path.exists(pattern):
            return True
    
    return False


def main():
    if len(sys.argv) != 2:
        print("Usage: python analyze_coverage.py <changed_files.txt>")
        sys.exit(1)
    
    changed_files = sys.argv[1]
    
    if not os.path.exists(changed_files):
        print(f"File {changed_files} not found")
        sys.exit(1)
    
    python_files = get_python_files(changed_files)
    
    missing_tests = []
    
    for file_path in python_files:
        if not os.path.exists(file_path):
            continue
            
        functions, classes = analyze_functions_and_classes(file_path)
        
        if functions or classes:
            if not check_existing_tests(file_path):
                missing_tests.append({
                    'file': file_path,
                    'functions': functions,
                    'classes': classes
                })
    
    if missing_tests:
        print("### Missing Test Coverage")
        print()
        for item in missing_tests:
            print(f"**{item['file']}**")
            if item['classes']:
                print(f"- Classes: {', '.join(item['classes'])}")
            if item['functions']:
                print(f"- Functions: {', '.join(item['functions'])}")
            print()
            
            # Suggest test structure
            print("Suggested test structure:")
            print(f"```python")
            print(f"# tests/unit/test_{os.path.basename(item['file'])}")
            print(f"import pytest")
            print(f"from {item['file'].replace('/', '.').replace('.py', '')} import *")
            print()
            
            for class_name in item['classes']:
                print(f"class Test{class_name}:")
                print(f"    def test_{class_name.lower()}_init(self):")
                print(f"        \"\"\"Test {class_name} initialization.\"\"\"")
                print(f"        pass")
                print()
            
            for func_name in item['functions']:
                print(f"def test_{func_name}():")
                print(f"    \"\"\"Test {func_name} function.\"\"\"")
                print(f"    pass")
                print()
            
            print("```")
            print()
    else:
        print("No obvious missing test coverage detected for changed files.")


if __name__ == "__main__":
    main()