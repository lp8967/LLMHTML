#!/usr/bin/env python3
"""
Main module to execute the full test suite.
Runs integration, RAG quality, and evaluator tests.
"""

import sys
import subprocess
import os


def run_all_tests():
    """
    Run all predefined test suites sequentially.

    Returns:
        bool: True if all tests passed successfully, False otherwise.
    """
    test_commands = [
        ["pytest", "tests/test_api_integration.py", "-v"],
        ["pytest", "tests/test_rag_quality.py", "-v"],
        ["pytest", "tests/test_rag_quality_metrics.py", "-v"],
        ["python", "tests/simple_evaluator.py"]
    ]

    print("Running Comprehensive Test Suite...")
    all_passed = True

    for i, cmd in enumerate(test_commands, 1):
        print(f"--- Test Suite {i}/{len(test_commands)}: {' '.join(cmd)} ---")

        try:
            # Run the test command and capture output
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                print(f"PASSED: {cmd[1]}")
                print(result.stdout)
            else:
                print(f"FAILED: {cmd[1]}")
                print("STDOUT:", result.stdout)
                print("STDERR:", result.stderr)
                all_passed = False

        except Exception as e:
            print(f"ERROR running {cmd}: {e}")
            all_passed = False

    return all_passed


if __name__ == "__main__":
    success = run_all_tests()

    if success:
        print("ALL TESTS PASSED SUCCESSFULLY!")
        sys.exit(0)
    else:
        print("SOME TESTS FAILED!")
        sys.exit(1)
