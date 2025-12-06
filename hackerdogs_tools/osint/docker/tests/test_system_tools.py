#!/usr/bin/env python3
"""
Test system-based OSINT tools in Docker container.

Validates --help/--version output and writes all outputs to files.
Tests: Masscan, ZMap, YARA, ExifTool
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


def run_docker_exec(tool: str, args: List[str], timeout: int = 30) -> Dict[str, any]:
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


def test_masscan_help() -> Tuple[bool, str, str]:
    """Test Masscan --help output and write to file."""
    print("  Testing Masscan (--help)...")
    result = run_docker_exec("masscan", ["--help"], timeout=30)
    
    stdout = result["stdout"] + result["stderr"]
    if not stdout.strip():
        return False, "❌ Masscan: No help output", ""
    
    # Write output to file
    output_file = write_output_to_file("masscan", stdout)
    
    if "usage" in stdout.lower() or "masscan" in stdout.lower() or "port" in stdout.lower():
        file_size = output_file.stat().st_size
        return True, f"✅ Masscan: Help output written to {output_file.name} ({file_size} bytes)", stdout[:200]
    else:
        return False, f"❌ Masscan: Invalid help output", stdout[:200]


def test_zmap_help() -> Tuple[bool, str, str]:
    """Test ZMap --help output and write to file."""
    print("  Testing ZMap (--help)...")
    result = run_docker_exec("zmap", ["--help"], timeout=30)
    
    stdout = result["stdout"] + result["stderr"]
    if not stdout.strip():
        return False, "❌ ZMap: No help output", ""
    
    # Write output to file
    output_file = write_output_to_file("zmap", stdout)
    
    if "usage" in stdout.lower() or "zmap" in stdout.lower() or "flags" in stdout.lower():
        file_size = output_file.stat().st_size
        return True, f"✅ ZMap: Help output written to {output_file.name} ({file_size} bytes)", stdout[:200]
    else:
        return False, f"❌ ZMap: Invalid help output", stdout[:200]


def test_yara_help() -> Tuple[bool, str, str]:
    """Test YARA --help output and write to file."""
    print("  Testing YARA (--help)...")
    result = run_docker_exec("yara", ["--help"], timeout=30)
    
    stdout = result["stdout"] + result["stderr"]
    if not stdout.strip():
        return False, "❌ YARA: No help output", ""
    
    # Write output to file
    output_file = write_output_to_file("yara", stdout)
    
    if "usage" in stdout.lower() or "yara" in stdout.lower() or "rules" in stdout.lower():
        file_size = output_file.stat().st_size
        return True, f"✅ YARA: Help output written to {output_file.name} ({file_size} bytes)", stdout[:200]
    else:
        return False, f"❌ YARA: Invalid help output", stdout[:200]


def test_exiftool_help() -> Tuple[bool, str, str]:
    """Test ExifTool --help output and write to file."""
    print("  Testing ExifTool (--help)...")
    result = run_docker_exec("exiftool", ["-h"], timeout=30)
    
    stdout = result["stdout"] + result["stderr"]
    if not stdout.strip():
        return False, "❌ ExifTool: No help output", ""
    
    # Write output to file
    output_file = write_output_to_file("exiftool", stdout)
    
    if "usage" in stdout.lower() or "exiftool" in stdout.lower() or "options" in stdout.lower():
        file_size = output_file.stat().st_size
        return True, f"✅ ExifTool: Help output written to {output_file.name} ({file_size} bytes)", stdout[:200]
    else:
        return False, f"❌ ExifTool: Invalid help output", stdout[:200]


def run_all_tests() -> Dict[str, any]:
    """Run all system tool tests."""
    print("=" * 80)
    print("Testing System-based OSINT Tools (Help Output Validation)")
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
        ("masscan", test_masscan_help),
        ("zmap", test_zmap_help),
        ("yara", test_yara_help),
        ("exiftool", test_exiftool_help),
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
        print("✅ All system tools passed!")
    else:
        print("❌ Some system tools failed")
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
