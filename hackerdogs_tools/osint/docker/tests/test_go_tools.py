#!/usr/bin/env python3
"""
Test Go-based OSINT tools in Docker container.

Validates --help output and writes all outputs to files.
Tests: Amass, Nuclei, Subfinder, waybackurls
"""

import subprocess
import sys
import json
from pathlib import Path
from typing import Dict, List, Tuple


CONTAINER_NAME = "osint-tools"
DOCKER_RUNTIME = "docker"
TEST_DIR = Path(__file__).parent
OUTPUT_DIR = TEST_DIR / "test_output"
OUTPUT_DIR.mkdir(exist_ok=True)


def run_docker_exec(tool: str, args: List[str], timeout: int = 60) -> Dict[str, any]:
    """Execute a tool in Docker container."""
    cmd = [DOCKER_RUNTIME, "exec", CONTAINER_NAME, tool] + args
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False
        )
        return {
            "tool": tool,
            "status": "success" if result.returncode == 0 else "error",
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "command": " ".join(cmd)
        }
    except subprocess.TimeoutExpired:
        return {
            "tool": tool,
            "status": "error",
            "returncode": -1,
            "stdout": "",
            "stderr": f"Command timed out after {timeout} seconds",
            "command": " ".join(cmd)
        }
    except Exception as e:
        return {
            "tool": tool,
            "status": "error",
            "returncode": -1,
            "stdout": "",
            "stderr": str(e),
            "command": " ".join(cmd)
        }


def write_output_to_file(tool_name: str, output: str, suffix: str = "help") -> Path:
    """Write output to a file in test_output directory."""
    output_file = OUTPUT_DIR / f"{tool_name}_{suffix}.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"Command: {tool_name} --help\n")
        f.write("=" * 80 + "\n")
        f.write(output)
        if not output.endswith('\n'):
            f.write('\n')
    return output_file


def test_amass_help() -> Tuple[bool, str, str]:
    """Test Amass --help output and write to file."""
    print("  Testing Amass (--help)...")
    result = run_docker_exec("amass", ["-help"], timeout=30)
    
    stdout = result["stdout"] + result["stderr"]
    if not stdout.strip():
        return False, "❌ Amass: No help output", ""
    
    # Write output to file
    output_file = write_output_to_file("amass", stdout)
    
    # Check for help indicators
    if "usage" in stdout.lower() or "flags" in stdout.lower() or "options" in stdout.lower() or "amass" in stdout.lower():
        file_size = output_file.stat().st_size
        return True, f"✅ Amass: Help output written to {output_file.name} ({file_size} bytes)", stdout[:200]
    else:
        return False, f"❌ Amass: Invalid help output", stdout[:200]


def test_nuclei_help() -> Tuple[bool, str, str]:
    """Test Nuclei --help output and write to file."""
    print("  Testing Nuclei (--help)...")
    result = run_docker_exec("nuclei", ["-h"], timeout=30)
    
    stdout = result["stdout"] + result["stderr"]
    if not stdout.strip():
        return False, "❌ Nuclei: No help output", ""
    
    # Write output to file
    output_file = write_output_to_file("nuclei", stdout)
    
    if "usage" in stdout.lower() or "flags" in stdout.lower() or "nuclei" in stdout.lower():
        file_size = output_file.stat().st_size
        return True, f"✅ Nuclei: Help output written to {output_file.name} ({file_size} bytes)", stdout[:200]
    else:
        return False, f"❌ Nuclei: Invalid help output", stdout[:200]


def test_subfinder_help() -> Tuple[bool, str, str]:
    """Test Subfinder --help output and write to file."""
    print("  Testing Subfinder (--help)...")
    result = run_docker_exec("subfinder", ["-h"], timeout=30)
    
    stdout = result["stdout"] + result["stderr"]
    if not stdout.strip():
        return False, "❌ Subfinder: No help output", ""
    
    # Write output to file
    output_file = write_output_to_file("subfinder", stdout)
    
    if "usage" in stdout.lower() or "flags" in stdout.lower() or "subfinder" in stdout.lower():
        file_size = output_file.stat().st_size
        return True, f"✅ Subfinder: Help output written to {output_file.name} ({file_size} bytes)", stdout[:200]
    else:
        return False, f"❌ Subfinder: Invalid help output", stdout[:200]


def test_waybackurls_help() -> Tuple[bool, str, str]:
    """Test waybackurls --help output and write to file."""
    print("  Testing waybackurls (--help)...")
    result = run_docker_exec("waybackurls", ["-h"], timeout=30)
    
    stdout = result["stdout"] + result["stderr"]
    if not stdout.strip():
        return False, "❌ waybackurls: No help output", ""
    
    # Write output to file
    output_file = write_output_to_file("waybackurls", stdout)
    
    if "usage" in stdout.lower() or "help" in stdout.lower() or "waybackurls" in stdout.lower():
        file_size = output_file.stat().st_size
        return True, f"✅ waybackurls: Help output written to {output_file.name} ({file_size} bytes)", stdout[:200]
    else:
        return False, f"❌ waybackurls: Invalid help output", stdout[:200]


def run_all_tests() -> Dict[str, any]:
    """Run all Go tool tests."""
    print("=" * 80)
    print("Testing Go-based OSINT Tools (Help Output Validation)")
    print("=" * 80)
    print(f"Output directory: {OUTPUT_DIR}")
    print("=" * 80)
    
    # Check if container is running
    try:
        check_result = subprocess.run(
            [DOCKER_RUNTIME, "ps", "--filter", f"name={CONTAINER_NAME}", "--format", "{{.Names}}"],
            capture_output=True,
            text=True,
            check=False
        )
        if CONTAINER_NAME not in check_result.stdout:
            return {
                "status": "error",
                "message": f"Container '{CONTAINER_NAME}' is not running. Start it with: docker-compose up -d",
                "results": {}
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to check container status: {str(e)}",
            "results": {}
        }
    
    results = {}
    all_passed = True
    
    # Test each tool
    tests = [
        ("amass", test_amass_help),
        ("nuclei", test_nuclei_help),
        ("subfinder", test_subfinder_help),
        ("waybackurls", test_waybackurls_help),
    ]
    
    for tool_name, test_func in tests:
        try:
            passed, message, output = test_func()
            results[tool_name] = {
                "passed": passed,
                "message": message,
                "output_sample": output[:200] if output else ""
            }
            if not passed:
                all_passed = False
            print(f"    {message}")
            if output:
                print(f"      Preview: {output[:150]}...")
        except Exception as e:
            results[tool_name] = {
                "passed": False,
                "message": f"❌ {tool_name} test exception: {str(e)}",
                "output_sample": ""
            }
            all_passed = False
            print(f"    ❌ {tool_name} test exception: {str(e)}")
    
    print("=" * 80)
    if all_passed:
        print("✅ All Go tools passed!")
    else:
        print("❌ Some Go tools failed")
    print(f"Output files saved to: {OUTPUT_DIR}")
    print("=" * 80)
    
    return {
        "status": "success" if all_passed else "error",
        "all_passed": all_passed,
        "results": results
    }


if __name__ == "__main__":
    result = run_all_tests()
    sys.exit(0 if result.get("all_passed", False) else 1)
