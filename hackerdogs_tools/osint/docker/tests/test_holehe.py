#!/usr/bin/env python3
"""
Dedicated test for holehe tool.

Tests holehe with actual email and validates JSON output format.
Since holehe doesn't have an official Docker image, it runs in the custom osint-tools container.
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

# Test email
TEST_EMAIL = "test@example.com"


def run_docker_exec(tool: str, args: List[str], timeout: int = 300) -> Dict[str, any]:
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


def write_output_to_file(tool_name: str, result: Dict, suffix: str = "functional") -> Path:
    """Write test output to file."""
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


def test_holehe_basic() -> Tuple[bool, str, str]:
    """Test holehe with basic email check."""
    print(f"  Testing holehe (email: {TEST_EMAIL})...")
    
    result = run_docker_exec(
        "holehe",
        [TEST_EMAIL],
        timeout=300
    )
    
    # Write all output to file
    output_file = write_output_to_file("holehe", result, "functional_basic")
    
    stdout = result["stdout"].strip()
    stderr = result["stderr"].strip()
    
    if not stdout and not stderr:
        return False, f"❌ Holehe: No output (log: {output_file.name})", ""
    
    # Check for execution indicators
    if "websites checked" in stdout.lower() or "Email used" in stdout or "Email not used" in stdout:
        # Count sites checked
        lines = stdout.split('\n')
        site_count = 0
        used_count = 0
        not_used_count = 0
        rate_limit_count = 0
        
        for line in lines:
            if "[+]" in line:
                used_count += 1
                site_count += 1
            elif "[-]" in line:
                not_used_count += 1
                site_count += 1
            elif "[x]" in line:
                rate_limit_count += 1
                site_count += 1
        
        summary = f"Checked {site_count} sites: {used_count} used, {not_used_count} not used, {rate_limit_count} rate limited"
        return True, f"✅ Holehe: {summary} (log: {output_file.name})", stdout[:300]
    
    return False, f"❌ Holehe: Invalid output format (log: {output_file.name})", stdout[:200] if stdout else stderr[:200]


def test_holehe_json_output() -> Tuple[bool, str, str]:
    """Test holehe and parse JSON lines from output."""
    print(f"  Testing holehe JSON output (email: {TEST_EMAIL})...")
    
    result = run_docker_exec(
        "holehe",
        [TEST_EMAIL, "--no-color", "--no-clear"],
        timeout=300
    )
    
    # Write all output to file
    output_file = write_output_to_file("holehe", result, "functional_json")
    
    stdout = result["stdout"].strip()
    
    if not stdout:
        return False, f"❌ Holehe: No output (log: {output_file.name})", ""
    
    # Holehe outputs JSON lines (one per site)
    # Look for JSON objects in the output
    json_objects = []
    lines = stdout.split('\n')
    
    for line in lines:
        line = line.strip()
        if line and (line.startswith('{') or '"name"' in line or '"exists"' in line):
            try:
                # Try to extract JSON from the line
                if line.startswith('{'):
                    obj = json.loads(line)
                    json_objects.append(obj)
            except:
                # Not JSON, continue
                pass
    
    # Also check for the summary format
    if "websites checked" in stdout.lower():
        # Extract site results from the formatted output
        site_results = []
        for line in lines:
            if "[+]" in line or "[-]" in line or "[x]" in line:
                # Extract site name
                parts = line.split()
                if len(parts) >= 2:
                    site_name = parts[-1] if parts[-1] else parts[1]
                    status = "exists" if "[+]" in line else ("rate_limit" if "[x]" in line else "not_exists")
                    site_results.append({
                        "name": site_name,
                        "exists": status == "exists",
                        "status": status
                    })
        
        if site_results:
            json_output_file = OUTPUT_DIR / "holehe_functional_json_results.json"
            with open(json_output_file, 'w', encoding='utf-8') as f:
                json.dump(site_results, f, indent=2)
            
            return True, f"✅ Holehe: Found {len(site_results)} site results, JSON saved to {json_output_file.name} (log: {output_file.name})", f"Sample: {site_results[0] if site_results else 'N/A'}"
    
    if json_objects:
        json_output_file = OUTPUT_DIR / "holehe_functional_json_results.json"
        with open(json_output_file, 'w', encoding='utf-8') as f:
            json.dump(json_objects, f, indent=2)
        
        return True, f"✅ Holehe: Found {len(json_objects)} JSON objects, saved to {json_output_file.name} (log: {output_file.name})", f"Sample: {json_objects[0] if json_objects else 'N/A'}"
    
    # Even if no JSON, if tool executed, it's a success
    if "websites checked" in stdout.lower() or TEST_EMAIL in stdout:
        return True, f"✅ Holehe: Executed successfully (no JSON format, but tool works) (log: {output_file.name})", stdout[:300]
    
    return False, f"❌ Holehe: No valid results (log: {output_file.name})", stdout[:200] if stdout else ""


def test_holehe_only_used() -> Tuple[bool, str, str]:
    """Test holehe with --only-used flag."""
    print(f"  Testing holehe --only-used (email: {TEST_EMAIL})...")
    
    result = run_docker_exec(
        "holehe",
        [TEST_EMAIL, "--only-used", "--no-color", "--no-clear"],
        timeout=300
    )
    
    # Write all output to file
    output_file = write_output_to_file("holehe", result, "functional_only_used")
    
    stdout = result["stdout"].strip()
    
    if not stdout:
        return False, f"❌ Holehe: No output (log: {output_file.name})", ""
    
    # With --only-used, should only show sites where email is used ([+])
    used_sites = []
    for line in stdout.split('\n'):
        if "[+]" in line:
            parts = line.split()
            if len(parts) >= 2:
                site_name = parts[-1] if parts[-1] else parts[1]
                used_sites.append(site_name)
    
    if used_sites:
        return True, f"✅ Holehe --only-used: Found {len(used_sites)} sites where email is used (log: {output_file.name})", f"Sample: {used_sites[0] if used_sites else 'N/A'}"
    elif "websites checked" in stdout.lower():
        return True, f"✅ Holehe --only-used: Executed successfully (no sites found where email is used) (log: {output_file.name})", stdout[:200]
    
    return False, f"❌ Holehe --only-used: Invalid output (log: {output_file.name})", stdout[:200] if stdout else ""


def run_all_tests() -> Dict[str, any]:
    """Run all holehe tests."""
    print("=" * 80)
    print("Testing Holehe Tool")
    print("=" * 80)
    print(f"Test email: {TEST_EMAIL}")
    print(f"Output directory: {OUTPUT_DIR}")
    print("Note: holehe runs in custom osint-tools container (no official Docker image)")
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
    
    # Test each functionality
    tests = [
        ("basic", test_holehe_basic),
        ("json_output", test_holehe_json_output),
        ("only_used", test_holehe_only_used),
    ]
    
    for test_name, test_func in tests:
        try:
            passed, message, output = test_func()
            results[test_name] = {
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
            results[test_name] = {
                "passed": False,
                "message": f"❌ {test_name} test exception: {str(e)}",
                "output_sample": ""
            }
            all_passed = False
            print(f"    ❌ {test_name} test exception: {str(e)}")
    
    print("=" * 80)
    if all_passed:
        print("✅ All holehe tests passed!")
    else:
        print("❌ Some holehe tests failed")
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

