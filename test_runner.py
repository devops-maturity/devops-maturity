#!/usr/bin/env python3
"""
Simple test runner for basic validation without external dependencies.

This script provides basic test structure validation and can run simple 
unit tests that don't require external packages.
"""

import sys
import os
import importlib.util
from pathlib import Path


def simple_test_runner():
    """Run basic tests that don't require external dependencies."""
    print("🧪 Running Basic Tests")
    print("=" * 40)
    
    # Test 1: Validate test file structure
    print("\n1. Testing file structure validation...")
    try:
        # Import and run our validation script
        spec = importlib.util.spec_from_file_location(
            "validate_tests", 
            Path(__file__).parent / "validate_tests.py"
        )
        validate_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(validate_module)
        
        result = validate_module.main()
        if result:
            print("   ✅ Test structure validation PASSED")
        else:
            print("   ❌ Test structure validation FAILED")
            return False
    except Exception as e:
        print(f"   ❌ Error during validation: {e}")
        return False
    
    # Test 2: Check that all test files are importable (syntax check)
    print("\n2. Testing test file syntax...")
    test_dir = Path(__file__).parent / "tests"
    test_files = list(test_dir.glob("test_*.py"))
    
    for test_file in test_files:
        try:
            with open(test_file, 'r') as f:
                compile(f.read(), test_file, 'exec')
            print(f"   ✅ {test_file.name} syntax valid")
        except SyntaxError as e:
            print(f"   ❌ {test_file.name} syntax error: {e}")
            return False
        except Exception as e:
            print(f"   ❌ {test_file.name} error: {e}")
            return False
    
    # Test 3: Verify test count
    print("\n3. Checking test coverage...")
    expected_test_files = [
        "test_core.py",
        "test_config.py", 
        "test_cli.py",
        "test_web.py",
        "test_database.py"
    ]
    
    found_files = [f.name for f in test_files]
    missing_files = set(expected_test_files) - set(found_files)
    
    if missing_files:
        print(f"   ❌ Missing test files: {missing_files}")
        return False
    else:
        print("   ✅ All expected test files present")
    
    print("\n" + "=" * 40)
    print("✅ All basic tests PASSED!")
    print("\n📋 Ready for full test execution with dependencies:")
    print("   - nox -s tests")
    print("   - pytest tests/")
    
    return True


if __name__ == "__main__":
    success = simple_test_runner()
    sys.exit(0 if success else 1)