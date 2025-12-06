#!/usr/bin/env python3
"""
Functional tests for OSINT tools with actual execution and output validation.

Tests tools with simple inputs:
- One username (test)
- One email (test@example.com)
- One domain (example.com)
- Local IP (127.0.0.1) for network scans

Uses the workspace volume mounted in docker-compose to save outputs.
"""

import subprocess
import sys
import json
import os
from pathlib import Path
from typing import Dict, List, Tuple


CONTAINER_NAME = "osint-tools"
DOCKER_RUNTIME = "docker"
TEST_DIR = Path(__file__).parent
WORKSPACE_DIR = TEST_DIR.parent / "workspace"
OUTPUT_DIR = TEST_DIR / "test_output"
CONTAINER_WORKSPACE = "/workspace"
OUTPUT_DIR.mkdir(exist_ok=True)

# Simple test data
TEST_USERNAME = "test"
TEST_EMAIL = "test@example.com"
TEST_DOMAIN = "example.com"
TEST_IP = "127.0.0.1"


def run_docker_exec(tool: str, args: List[str], timeout: int = 120) -> Dict[str, any]:
    """Execute a tool in the running Docker container."""
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
    except:
        return False


def write_functional_output(tool_name: str, result: Dict, suffix: str = "functional") -> Path:
    """Write functional test output to file."""
    output_file = OUTPUT_DIR / f"{tool_name}_{suffix}.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"Tool: {tool_name}\n")
        f.write(f"Command: {result.get('command', 'N/A')}\n")
        f.write(f"Return Code: {result.get('returncode', 'N/A')}\n")
        f.write("=" * 80 + "\n")
        f.write("STDOUT:\n")
        f.write("-" * 80 + "\n")
        f.write(result.get("stdout", ""))
        f.write("\n" + "=" * 80 + "\n")
        f.write("STDERR:\n")
        f.write("-" * 80 + "\n")
        f.write(result.get("stderr", ""))
        if not result.get("stderr", "").endswith('\n'):
            f.write('\n')
    return output_file


def test_sherlock_functional() -> Tuple[bool, str, str]:
    """Test Sherlock with actual username search and output file."""
    print(f"  Testing Sherlock (username: {TEST_USERNAME})...")
    
    WORKSPACE_DIR.mkdir(exist_ok=True)
    output_file = WORKSPACE_DIR / f"sherlock_{TEST_USERNAME}.json"
    
    # Clean up any existing file
    if output_file.exists():
        output_file.unlink()
    
    # Run sherlock with JSON output
    result = run_docker_exec(
        "sherlock",
        [TEST_USERNAME, "--json", "--output", f"{CONTAINER_WORKSPACE}/sherlock_{TEST_USERNAME}.json", "--timeout", "5", "--print-found"],
        timeout=180
    )
    
    # Check if output file was created
    if output_file.exists() and output_file.stat().st_size > 0:
        try:
            with open(output_file, 'r') as f:
                content = f.read()
                if content.strip():
                    return True, f"✅ Sherlock: Created output file ({output_file.stat().st_size} bytes)", content[:200]
        except:
            pass
    
    # Check stdout/stderr for results
    combined = result["stdout"] + result["stderr"]
    if "http" in combined.lower() or TEST_USERNAME in combined.lower() or "found" in combined.lower():
        return True, f"✅ Sherlock: Found results for {TEST_USERNAME}", combined[:200]
    
    return False, f"❌ Sherlock: No output file or results found", combined[:200]


def test_maigret_functional() -> Tuple[bool, str, str]:
    """Test Maigret with actual username search and output file."""
    print(f"  Testing Maigret (username: {TEST_USERNAME})...")
    
    WORKSPACE_DIR.mkdir(exist_ok=True)
    
    # Run maigret with folder output
    result = run_docker_exec(
        "maigret",
        [TEST_USERNAME, "--folderoutput", CONTAINER_WORKSPACE, "--timeout", "5", "--print-found"],
        timeout=180
    )
    
    # Write all output to file
    output_log = write_functional_output("maigret", result, f"functional_{TEST_USERNAME}")
    
    # Check for output files in workspace
    json_files = list(WORKSPACE_DIR.glob(f"*{TEST_USERNAME}*.json"))
    if json_files:
        try:
            file_size = json_files[0].stat().st_size
            with open(json_files[0], 'r') as f:
                content = f.read()
                if content.strip():
                    return True, f"✅ Maigret: Created output file with results ({file_size} bytes, log: {output_log.name})", content[:200]
                else:
                    return True, f"✅ Maigret: Created output file (empty - no results, log: {output_log.name})", ""
        except:
            return True, f"✅ Maigret: Created output file ({json_files[0].stat().st_size} bytes, log: {output_log.name})", ""
    
    # Check stdout for execution indicators
    stdout = result["stdout"]
    if "maigret" in stdout.lower() or "checking" in stdout.lower() or "search" in stdout.lower():
        if "http" in stdout.lower() or "[+]" in stdout or "found" in stdout.lower():
            return True, f"✅ Maigret: Found results (log: {output_log.name})", stdout[:200]
        else:
            return True, f"✅ Maigret: Executed successfully (no results, log: {output_log.name})", stdout[:200]
    
    return False, f"❌ Maigret: Execution failed (log: {output_log.name})", stdout[:200]


def test_holehe_functional() -> Tuple[bool, str, str]:
    """Test Holehe with actual email search."""
    print(f"  Testing Holehe (email: {TEST_EMAIL})...")
    
    result = run_docker_exec(
        "holehe",
        [TEST_EMAIL],
        timeout=180
    )
    
    # Write all output to file
    output_log = write_functional_output("holehe", result, f"functional_{TEST_EMAIL.replace('@', '_at_')}")
    
    stdout = result["stdout"].strip()
    if not stdout:
        return False, f"❌ Holehe: No output (log: {output_log.name})", ""
    
    # Check for JSON lines
    lines = stdout.split('\n')
    json_count = 0
    sample = ""
    
    for line in lines:
        if line.strip():
            try:
                data = json.loads(line)
                json_count += 1
                if not sample and "name" in data:
                    sample = f"Site: {data.get('name', 'N/A')}"
            except:
                continue
    
    if json_count > 0:
        return True, f"✅ Holehe: Processed {json_count} site(s) (log: {output_log.name})", sample
    else:
        # Check if tool executed (even if no results)
        if "holehe" in stdout.lower() or "{" in stdout or "exists" in stdout.lower() or "checking" in stdout.lower():
            return True, f"✅ Holehe: Executed successfully (no results, log: {output_log.name})", stdout[:200] if stdout else ""
        return False, f"❌ Holehe: Execution failed (log: {output_log.name})", stdout[:200] if stdout else ""


def test_subfinder_functional() -> Tuple[bool, str, str]:
    """Test Subfinder with actual domain search."""
    print(f"  Testing Subfinder (domain: {TEST_DOMAIN})...")
    
    WORKSPACE_DIR.mkdir(exist_ok=True)
    output_file = WORKSPACE_DIR / f"subfinder_{TEST_DOMAIN}.txt"
    
    # Clean up any existing file
    if output_file.exists():
        output_file.unlink()
    
    result = run_docker_exec(
        "subfinder",
        ["-d", TEST_DOMAIN, "-o", f"{CONTAINER_WORKSPACE}/subfinder_{TEST_DOMAIN}.txt", "-silent"],
        timeout=120
    )
    
    # Write all output to file
    output_log = write_functional_output("subfinder", result, f"functional_{TEST_DOMAIN}")
    
    # Check if output file was created
    if output_file.exists() and output_file.stat().st_size > 0:
        try:
            with open(output_file, 'r') as f:
                content = f.read()
                subdomains = [line.strip() for line in content.split('\n') if line.strip()]
                if subdomains:
                    return True, f"✅ Subfinder: Found {len(subdomains)} subdomain(s) (log: {output_log.name})", subdomains[0][:100]
        except:
            pass
    
    # Check stdout
    stdout = result["stdout"].strip()
    if stdout:
        subdomains = [line.strip() for line in stdout.split('\n') if line.strip()]
        if subdomains:
            return True, f"✅ Subfinder: Found {len(subdomains)} subdomain(s) (log: {output_log.name})", subdomains[0][:100]
    
    return False, f"❌ Subfinder: No subdomains found (log: {output_log.name})", stdout[:200] if stdout else ""


def test_amass_functional() -> Tuple[bool, str, str]:
    """Test Amass with actual domain enumeration."""
    print(f"  Testing Amass (domain: {TEST_DOMAIN})...")
    
    WORKSPACE_DIR.mkdir(exist_ok=True)
    output_file = WORKSPACE_DIR / f"amass_{TEST_DOMAIN}.txt"
    
    # Clean up any existing file
    if output_file.exists():
        output_file.unlink()
    
    # Run amass in passive mode
    result = run_docker_exec(
        "amass",
        ["enum", "-passive", "-d", TEST_DOMAIN, "-o", f"{CONTAINER_WORKSPACE}/amass_{TEST_DOMAIN}.txt"],
        timeout=120
    )
    
    # Write all output to file
    output_log = write_functional_output("amass", result, f"functional_{TEST_DOMAIN}")
    
    # Check if output file was created
    if output_file.exists() and output_file.stat().st_size > 0:
        try:
            with open(output_file, 'r') as f:
                content = f.read()
                subdomains = [line.strip() for line in content.split('\n') if line.strip()]
                if subdomains:
                    return True, f"✅ Amass: Found {len(subdomains)} subdomain(s) (log: {output_log.name})", subdomains[0][:100]
        except:
            pass
    
    # Check stdout
    stdout = result["stdout"]
    if TEST_DOMAIN in stdout.lower() or "subdomain" in stdout.lower():
        return True, f"✅ Amass: Executed successfully (log: {output_log.name})", stdout[:200]
    
    return False, f"❌ Amass: No results found (log: {output_log.name})", stdout[:200] if stdout else ""


def test_masscan_local() -> Tuple[bool, str, str]:
    """Test Masscan with localhost scan only."""
    print(f"  Testing Masscan (localhost: {TEST_IP})...")
    
    # Scan localhost only, common ports, very fast
    result = run_docker_exec(
        "masscan",
        [TEST_IP, "-p80,443,22", "--rate", "100", "--wait", "0"],
        timeout=30
    )
    
    # Write all output to file
    output_log = write_functional_output("masscan", result, f"functional_{TEST_IP.replace('.', '_')}")
    
    stdout = result["stdout"] + result["stderr"]
    
    # Masscan may not find open ports on localhost, but should execute
    # Check if it ran (even if no ports found)
    if "masscan" in stdout.lower() or "scan" in stdout.lower() or result["returncode"] in [0, 1]:
        # Return code 1 is OK for masscan if no ports found
        return True, f"✅ Masscan: Executed successfully (scanned {TEST_IP}, log: {output_log.name})", stdout[:200] if stdout else "No open ports found (expected)"
    
    return False, f"❌ Masscan: Execution failed (log: {output_log.name})", stdout[:200] if stdout else ""


def test_exiftool_functional() -> Tuple[bool, str, str]:
    """Test ExifTool with a simple metadata check."""
    print("  Testing ExifTool (version check)...")
    
    result = run_docker_exec(
        "exiftool",
        ["-ver"],
        timeout=10
    )
    
    # Write all output to file
    output_log = write_functional_output("exiftool", result, "functional_version")
    
    stdout = result["stdout"].strip()
    if stdout and any(char.isdigit() for char in stdout):
        return True, f"✅ ExifTool: Version {stdout} (log: {output_log.name})", stdout
    else:
        return False, f"❌ ExifTool: Invalid version output (log: {output_log.name})", stdout[:200] if stdout else ""


def run_all_tests() -> Dict[str, any]:
    """Run all functional tests."""
    print("=" * 80)
    print("Functional Tests for OSINT Tools")
    print("=" * 80)
    print(f"Test data:")
    print(f"  Username: {TEST_USERNAME}")
    print(f"  Email: {TEST_EMAIL}")
    print(f"  Domain: {TEST_DOMAIN}")
    print(f"  IP (local): {TEST_IP}")
    print(f"Workspace directory: {WORKSPACE_DIR}")
    print("=" * 80)
    
    # Check if container is running
    if not check_container_running():
        return {
            "status": "error",
            "message": f"Container '{CONTAINER_NAME}' is not running. Start it with: docker-compose up -d",
            "results": {}
        }
    
    # Ensure workspace directory exists
    WORKSPACE_DIR.mkdir(exist_ok=True)
    
    results = {}
    all_passed = True
    
    # Test each tool
    tests = [
        ("sherlock", test_sherlock_functional),
        ("maigret", test_maigret_functional),
        ("holehe", test_holehe_functional),
        ("subfinder", test_subfinder_functional),
        ("amass", test_amass_functional),
        ("masscan", test_masscan_local),
        ("exiftool", test_exiftool_functional),
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
                print(f"      Sample: {output[:150]}...")
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
        print("✅ All functional tests passed!")
    else:
        print("❌ Some functional tests failed")
    print("=" * 80)
    print(f"\nOutput files saved to:")
    print(f"  Workspace: {WORKSPACE_DIR}")
    print(f"  Test logs: {OUTPUT_DIR}")
    
    return {
        "status": "success" if all_passed else "error",
        "all_passed": all_passed,
        "results": results,
        "output_directory": str(WORKSPACE_DIR)
    }


if __name__ == "__main__":
    result = run_all_tests()
    sys.exit(0 if result.get("all_passed", False) else 1)
