#!/usr/bin/env python3
"""
Главный модуль для запуска всех тестов
"""

import sys
import subprocess
import os

def run_all_tests():
    """Запускает все тесты и возвращает успешность"""
    
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