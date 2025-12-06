#!/usr/bin/env python3
"""
Main test runner for all OSINT tools in Docker container.

Runs all test suites:
1. Go tools (Amass, Nuclei, Subfinder, waybackurls)
2. System tools (Masscan, ZMap, YARA, ExifTool)
3. Python tools (sublist3r, dnsrecon, theHarvester, sherlock, maigret, ghunt, holehe, etc.)
"""

import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, List
from datetime import datetime


CONTAINER_NAME = "osint-tools"
DOCKER_RUNTIME = "docker"
TEST_DIR = Path(__file__).parent


def check_container_running() -> bool:
    """Check if the osint-tools container is running."""
    try:
        result = subprocess.run(
            [DOCKER_RUNTIME, "ps", "--filter", f"name={CONTAINER_NAME}", "--format", "{{.Names}}"],
            capture_output=True,
            text=True,
            check=False
        )
        return CONTAINER_NAME in result.stdout
    except Exception:
        return False


def run_test_suite(test_file: str) -> Dict[str, any]:
    """Run a test suite script by importing and calling its run_all_tests function."""
    test_path = TEST_DIR / test_file
    if not test_path.exists():
        return {
            "status": "error",
            "message": f"Test file not found: {test_file}",
            "results": {}
        }
    
    try:
        # Import the test module dynamically
        import importlib.util
        spec = importlib.util.spec_from_file_location("test_module", test_path)
        if spec is None or spec.loader is None:
            return {
                "status": "error",
                "message": f"Failed to load test module: {test_file}",
                "results": {}
            }
        
        test_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(test_module)
        
        # Call the run_all_tests function
        if hasattr(test_module, "run_all_tests"):
            result = test_module.run_all_tests()
            return result
        else:
            return {
                "status": "error",
                "message": f"Test module {test_file} does not have run_all_tests() function",
                "results": {}
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to run test suite {test_file}: {str(e)}",
            "results": {},
            "error": str(e)
        }


def main():
    """Run all test suites."""
    print("=" * 80)
    print("OSINT Tools Docker Container Test Suite")
    print("=" * 80)
    print(f"Container: {CONTAINER_NAME}")
    print(f"Test directory: {TEST_DIR}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 80)
    
    # Check if container is running
    if not check_container_running():
        print(f"\n❌ ERROR: Container '{CONTAINER_NAME}' is not running!")
        print(f"\nTo start the container:")
        print(f"  cd {TEST_DIR.parent}")
        print(f"  docker-compose up -d")
        print(f"\nOr manually:")
        print(f"  docker run -d --name {CONTAINER_NAME} osint-tools:latest")
        sys.exit(1)
    
    print(f"\n✅ Container '{CONTAINER_NAME}' is running\n")
    
    # Test suites to run
    test_suites = [
        ("Go Tools", "test_go_tools.py"),
        ("System Tools", "test_system_tools.py"),
        ("Python Tools", "test_python_tools.py"),
    ]
    
    all_results = {}
    overall_success = True
    
    # Run each test suite
    for suite_name, test_file in test_suites:
        print(f"\n{'=' * 80}")
        print(f"Running {suite_name} Tests")
        print(f"{'=' * 80}\n")
        
        suite_result = run_test_suite(test_file)
        all_results[suite_name] = suite_result
        
        # Print summary based on all_passed flag
        if suite_result.get("all_passed", False):
            print(f"\n✅ {suite_name}: All tests passed")
        else:
            print(f"\n❌ {suite_name}: Some tests failed")
            overall_success = False
    
    # Final summary
    print("\n" + "=" * 80)
    print("Test Suite Summary")
    print("=" * 80)
    
    total_tests = 0
    passed_tests = 0
    
    for suite_name, suite_result in all_results.items():
        results = suite_result.get("results", {})
        suite_passed = sum(1 for r in results.values() if r.get("passed", False))
        suite_total = len(results)
        total_tests += suite_total
        passed_tests += suite_passed
        
        status = "✅" if suite_result.get("all_passed", False) else "❌"
        print(f"{status} {suite_name}: {suite_passed}/{suite_total} tests passed")
    
    print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
    
    if overall_success:
        print("\n✅ All test suites passed!")
    else:
        print("\n❌ Some test suites failed")
        print("\nDetailed results:")
        for suite_name, suite_result in all_results.items():
            print(f"\n{suite_name}:")
            results = suite_result.get("results", {})
            for tool_name, tool_result in results.items():
                status = "✅" if tool_result.get("passed", False) else "❌"
                print(f"  {status} {tool_name}: {tool_result.get('message', 'N/A')}")
    
    print("=" * 80)
    
    # Save results to JSON file
    results_file = TEST_DIR / f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "container": CONTAINER_NAME,
            "overall_success": overall_success,
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": total_tests - passed_tests
            },
            "results": all_results
        }, f, indent=2)
    
    print(f"\n📁 Detailed results saved to: {results_file}")
    
    sys.exit(0 if overall_success else 1)


if __name__ == "__main__":
    main()

