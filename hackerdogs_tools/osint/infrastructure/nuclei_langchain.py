"""
Nuclei Tool for LangChain Agents

Template-based vulnerability scanner using ProjectDiscovery Nuclei.
"""

import json
import subprocess
from typing import Optional, List
from langchain.tools import tool, ToolRuntime
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error
from hackerdogs_tools.osint.docker_client import get_docker_client, execute_in_docker

logger = setup_logger(__name__, log_file_path="logs/nuclei_tool.log")


def _check_docker_available() -> bool:
    """Check if Docker is available for running Nuclei in container."""
    client = get_docker_client()
    return client is not None and client.docker_available


@tool
def nuclei_scan(
    runtime: ToolRuntime,
    target: str,
    templates: Optional[List[str]] = None,
    severity: Optional[str] = None,
    tags: Optional[List[str]] = None,
    rate_limit: Optional[int] = None,
    concurrency: Optional[int] = None
) -> str:
    """
    Scan target for vulnerabilities using Nuclei templates.
    
    Nuclei is a fast vulnerability scanner based on templates.
    It can detect CVEs, misconfigurations, and security issues.
    
    Best practices:
    - Use rate limiting to avoid overwhelming targets
    - Filter by severity to focus on critical issues
    - Use specific templates for targeted scanning
    - Regularly update templates: nuclei -update-templates
    
    Args:
        runtime: ToolRuntime instance (automatically injected).
        target: URL or IP to scan (e.g., "https://example.com" or "192.168.1.1").
        templates: Specific template IDs to use (default: all templates).
        severity: Filter by severity level. Options: "info", "low", "medium", "high", "critical".
                  Can specify multiple: "critical,high" (default: all severities).
        tags: Filter by template tags (e.g., ["cve", "xss", "sqli"]).
        rate_limit: Maximum requests per second (default: None, uses Nuclei default).
                    Recommended: 50-150 for production targets.
        concurrency: Number of concurrent requests (default: None, uses Nuclei default).
                     Recommended: 25-50 for most targets.
    
    Returns:
        JSON string with vulnerability findings including:
        - status: "success" or "error"
        - target: Scanned target
        - findings: List of vulnerability findings
        - count: Number of findings
        - execution_method: "docker" or "official_docker_image"
    """
    try:
        safe_log_info(logger, f"[nuclei_scan] Starting scan", target=target)
        
        # Docker-only execution
        if not _check_docker_available():
            error_msg = (
                "Docker is required for OSINT tools. Setup:\n"
                "1. Build Docker image: cd hackerdogs_tools/osint/docker && docker build -t osint-tools:latest .\n"
                "2. Start container: docker-compose up -d"
            )
            safe_log_error(logger, error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        # Build Nuclei command arguments
        # Reference: https://docs.projectdiscovery.io/opensource/nuclei/usage
        args = ["-u", target, "-jsonl", "-o", "-"]
        
        # Template selection
        if templates:
            args.extend(["-t", ",".join(templates)])
        
        # Severity filtering (e.g., "critical,high" or "critical")
        if severity:
            args.extend(["-severity", severity])
        
        # Tag filtering
        if tags:
            args.extend(["-tags", ",".join(tags)])
        
        # Rate limiting (requests per second)
        if rate_limit:
            args.extend(["-rate-limit", str(rate_limit)])
        
        # Concurrency control
        if concurrency:
            args.extend(["-c", str(concurrency)])
        
        # Execute in Docker (uses official projectdiscovery/nuclei image if available)
        docker_result = execute_in_docker("nuclei", args, timeout=600)
        
        # Nuclei exit codes:
        # 0 = Success, no findings
        # 1 = Success, findings found (not an error)
        # >1 = Actual error
        returncode = docker_result.get("returncode", -1)
        if docker_result["status"] != "success" and returncode not in [0, 1]:
            error_msg = f"Nuclei scan failed: {docker_result.get('stderr', docker_result.get('message', 'Unknown error'))}"
            safe_log_error(logger, error_msg, returncode=returncode)
            return json.dumps({"status": "error", "message": error_msg, "returncode": returncode})
        
        findings = []
        stdout = docker_result.get("stdout", "")
        for line in stdout.strip().split('\n'):
            if not line.strip():
                continue
            try:
                findings.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        
        result_data = {
            "status": "success",
            "target": target,
            "findings": findings,
            "count": len(findings),
            "execution_method": docker_result.get("execution_method", "docker"),
            "user_id": runtime.state.get("user_id", "")
        }
        
        safe_log_info(logger, f"[nuclei_scan] Complete", target=target, count=result_data["count"])
        return json.dumps(result_data, indent=2)
        
    except subprocess.TimeoutExpired:
        error_msg = "Nuclei scan timed out after 600 seconds"
        safe_log_error(logger, f"[nuclei_scan] {error_msg}", target=target)
        return json.dumps({"status": "error", "message": error_msg})
    except Exception as e:
        safe_log_error(logger, f"[nuclei_scan] Unexpected error: {str(e)}", target=target, exc_info=True)
        return json.dumps({"status": "error", "message": f"Unexpected error: {str(e)}"})

