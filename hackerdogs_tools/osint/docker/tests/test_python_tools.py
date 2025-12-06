#!/usr/bin/env python3
"""
Test Python-based OSINT tools in Docker container.

Validates --help output and module imports, writes all outputs to files.
Tests: sherlock, maigret, holehe, and Python modules
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


def test_sherlock_help() -> Tuple[bool, str, str]:
    """Test Sherlock --help output and write to file."""
    print("  Testing Sherlock (--help)...")
    result = run_docker_exec("sherlock", ["--help"], timeout=30)
    
    stdout = result["stdout"] + result["stderr"]
    if not stdout.strip():
        return False, "❌ Sherlock: No help output", ""
    
    # Write output to file
    output_file = write_output_to_file("sherlock", stdout)
    
    if "usage" in stdout.lower() or "sherlock" in stdout.lower() or "username" in stdout.lower():
        file_size = output_file.stat().st_size
        return True, f"✅ Sherlock: Help output written to {output_file.name} ({file_size} bytes)", stdout[:200]
    else:
        return False, f"❌ Sherlock: Invalid help output", stdout[:200]


def test_maigret_help() -> Tuple[bool, str, str]:
    """Test Maigret --help output and write to file."""
    print("  Testing Maigret (--help)...")
    result = run_docker_exec("maigret", ["--help"], timeout=30)
    
    stdout = result["stdout"] + result["stderr"]
    if not stdout.strip():
        return False, "❌ Maigret: No help output", ""
    
    # Write output to file
    output_file = write_output_to_file("maigret", stdout)
    
    if "usage" in stdout.lower() or "maigret" in stdout.lower() or "username" in stdout.lower():
        file_size = output_file.stat().st_size
        return True, f"✅ Maigret: Help output written to {output_file.name} ({file_size} bytes)", stdout[:200]
    else:
        return False, f"❌ Maigret: Invalid help output", stdout[:200]


def test_holehe_help() -> Tuple[bool, str, str]:
    """Test Holehe --help output and write to file."""
    print("  Testing Holehe (--help)...")
    result = run_docker_exec("holehe", ["--help"], timeout=30)
    
    stdout = result["stdout"] + result["stderr"]
    if not stdout.strip():
        return False, "❌ Holehe: No help output", ""
    
    # Write output to file
    output_file = write_output_to_file("holehe", stdout)
    
    if "usage" in stdout.lower() or "holehe" in stdout.lower() or "email" in stdout.lower():
        file_size = output_file.stat().st_size
        return True, f"✅ Holehe: Help output written to {output_file.name} ({file_size} bytes)", stdout[:200]
    else:
        return False, f"❌ Holehe: Invalid help output", stdout[:200]


def test_python_module(module_name: str, import_name: str = None) -> Tuple[bool, str, str]:
    """Test if a Python module can be imported and write result to file."""
    if import_name is None:
        import_name = module_name
    
    test_code = f"import {import_name}; print('OK')"
    cmd = [DOCKER_RUNTIME, "exec", CONTAINER_NAME, "python3", "-c", test_code]
    
    output_file = OUTPUT_DIR / f"{module_name}_import.txt"
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10, check=False)
        
        # Write output to file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"Command: python3 -c 'import {import_name}; print(\"OK\")'\n")
            f.write("=" * 80 + "\n")
            f.write(f"Return code: {result.returncode}\n")
            f.write(f"Stdout: {result.stdout}\n")
            f.write(f"Stderr: {result.stderr}\n")
        
        if result.returncode == 0 and "OK" in result.stdout:
            file_size = output_file.stat().st_size
            return True, f"✅ {module_name}: Import successful (output: {output_file.name})", result.stdout.strip()
        else:
            error = result.stderr or result.stdout
            return False, f"❌ {module_name} failed: {error[:100]}", ""
    except Exception as e:
        # Write error to file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"Command: python3 -c 'import {import_name}; print(\"OK\")'\n")
            f.write("=" * 80 + "\n")
            f.write(f"Exception: {str(e)}\n")
        return False, f"❌ {module_name} exception: {str(e)}", ""


def run_all_tests() -> Dict[str, any]:
    """Run all Python tool tests."""
    print("=" * 80)
    print("Testing Python-based OSINT Tools (Help Output & Module Validation)")
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
    
    # Test CLI tools with --help
    print("\nTesting CLI tools (--help output)...")
    cli_tests = [
        ("sherlock", test_sherlock_help),
        ("maigret", test_maigret_help),
        ("holehe", test_holehe_help),
    ]
    
    for tool_name, test_func in cli_tests:
        try:
            passed, message, output = test_func()
            results[f"{tool_name}_cli"] = {
                "passed": passed,
                "message": message,
                "output_sample": output[:200] if output else "",
                "type": "cli"
            }
            if not passed:
                all_passed = False
            print(f"    {message}")
            if output:
                print(f"      Preview: {output[:150]}...")
        except Exception as e:
            results[f"{tool_name}_cli"] = {
                "passed": False,
                "message": f"❌ {tool_name} CLI test exception: {str(e)}",
                "output_sample": "",
                "type": "cli"
            }
            all_passed = False
            print(f"    ❌ {tool_name} CLI test exception: {str(e)}")
    
    # Test Python modules (import-based)
    print("\nTesting Python module imports...")
    module_tests = [
        ("sublist3r", "sublist3r"),
        ("dnsrecon", "dnsrecon"),
        ("maigret", "maigret"),
        ("holehe", "holehe"),
        ("scrapy", "scrapy"),
        ("waybackpy", "waybackpy"),
        ("internetarchive", "internetarchive"),
        ("exifread", "exifread"),
        ("piexif", "piexif"),
        ("yara", "yara"),
    ]
    
    for module_name, import_name in module_tests:
        try:
            passed, message, output = test_python_module(module_name, import_name)
            results[module_name] = {
                "passed": passed,
                "message": message,
                "output_sample": output[:200] if output else "",
                "type": "module"
            }
            if not passed:
                all_passed = False
            print(f"    {message}")
        except Exception as e:
            results[module_name] = {
                "passed": False,
                "message": f"❌ {module_name} test exception: {str(e)}",
                "output_sample": "",
                "type": "module"
            }
            all_passed = False
            print(f"    ❌ {module_name} test exception: {str(e)}")
    
    print("=" * 80)
    if all_passed:
        print("✅ All Python tools passed!")
    else:
        print("❌ Some Python tools failed")
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
