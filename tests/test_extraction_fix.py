#!/usr/bin/env python3
"""
Comprehensive test suite for extraction functions.
"""

import sys
from pathlib import Path

# Add parent directory to Python path so we can import pyuvstarter directly
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import pyuvstarter module directly
import pyuvstarter

def test_function(function_name, test_cases):
    """Test a function with various test cases."""
    print("\n=== Testing {} ===".format(function_name))

    failed_tests = []
    passed_tests = []

    for i, (input_desc, expected, should_pass) in enumerate(test_cases, 1):
        result = None
        try:
            result = function_name(input_desc)
            if result == expected:
                status = "PASS"
                passed_tests.append((input_desc, expected, result))
            else:
                status = "FAIL (expected '{}', got '{}')".format(expected, result)
                failed_tests.append((input_desc, expected, result))
        except Exception as e:
            status = "EXCEPTION: {}".format(e)
            failed_tests.append((input_desc, expected, str(e)))
        print("{}: {}".format(i, status))
        print("   Input: {}".format(repr(input_desc)))
        print("   Expected: {}".format(repr(expected)))
        print("   Result: {}".format(repr(result)))
        print()

    print("\n=== Results for {} ===".format(function_name))
    print("Passed: {}/{}".format(len(passed_tests), len(test_cases)))

    if failed_tests:
        print("\n=== Failed Tests ===")
        for input_desc, expected, result in failed_tests:
            print("Input: {}".format(repr(input_desc)))
            print("Expected: {}".format(repr(expected)))
            print("Result: {}".format(repr(result)))
            print()

    return len(failed_tests) == 0

def main():
    print("Testing pyuvstarter package name extraction functions...")

    # Test cases for string function
    string_test_cases = [
        ("numpy>=1.19.0", "numpy", True),
        ("requests[security]>=2.25.0", "requests", True),
        ("Django>=3.0,<4.0", "django", True),
        ("package==2.1.3", "package", True),
        ("package[extra]>=1.0.0", "package", True),
        ("my-package>=1.0.0", "my-package", True),
        ("", "", True),
        (None, "", True),
        ("invalid@@specifier", "invalid", True),
        ("scikit-learn>=1.0.0,<2.0.0", "scikit-learn", True),
        ("Pillow>=10.0.0", "pillow", True),  # Case normalization
    ]

    string_function_passed = test_function(pyuvstarter._extract_package_name_from_specifier, string_test_cases)

    # Test cases for tuple function
    tuple_test_cases = [
        (("numpy", "numpy>=1.19.0"), "numpy", True),
        (("requests", "requests[security]>=2.25.0"), "requests", True),
        (("my-package", "my-package>=1.0.0"), "my-package", True),
        (("", "empty-string"), "empty-string", True),
        (("only-name", "only-name"), "only-name", True),
        (("name", "specifier", "extras"), "name", True),
        (None, "", True),  # Should handle None gracefully
        (("name", "specifier", "extras"), "name", True),
    ]

    tuple_function_passed = test_function(pyuvstarter._extract_package_name_from_dependency_tuple, tuple_test_cases)

    print("\n" + "="*80)
    print("String function tests passed: {}".format("PASS" if string_function_passed else "FAIL"))
    print("Tuple function tests passed: {}".format("PASS" if tuple_function_passed else "FAIL"))

    overall_passed = string_function_passed and tuple_function_passed
    print("\nOverall: {}".format("ALL TESTS PASSED" if overall_passed else "SOME TESTS FAILED"))

    return 0 if overall_passed else 1

if __name__ == "__main__":
    sys.exit(main())