"""
Nuclei Tool for LangChain Agents

Template-based vulnerability scanner using ProjectDiscovery Nuclei.
"""

import json
import subprocess
import shutil
from typing import Optional, List
from langchain.tools import tool, ToolRuntime
from langchain.agents import AgentState
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error
from hackerdogs_tools.osint.docker_client import get_docker_client, execute_in_docker

logger = setup_logger(__name__, log_file_path="logs/nuclei_tool.log")


class NucleiSecurityAgentState(AgentState):
    """Extended agent state for Nuclei operations."""
    user_id: str = ""


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
    tags: Optional[List[str]] = None
) -> str:
    """
    Scan target for vulnerabilities using Nuclei templates.
    
    Nuclei is a fast vulnerability scanner based on templates.
    It can detect CVEs, misconfigurations, and security issues.
    
    Args:
        runtime: ToolRuntime instance (automatically injected).
        target: URL or IP to scan.
        templates: Specific template IDs (default: all).
        severity: Filter by severity (info, low, medium, high, critical).
        tags: Filter by tags.
    
    Returns:
        JSONL string with vulnerability findings.
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
        
        args = ["-u", target, "-jsonl", "-o", "-"]
        if templates:
            args.extend(["-t", ",".join(templates)])
        if severity:
            args.extend(["-severity", severity])
        if tags:
            args.extend(["-tags", ",".join(tags)])
        
        # Execute in Docker
        docker_result = execute_in_docker("nuclei", args, timeout=600)
        
        # Exit code 1 can mean findings were found (not an error)
        if docker_result["status"] != "success" and docker_result.get("returncode", -1) not in [0, 1]:
            error_msg = f"Nuclei scan failed: {docker_result.get('stderr', docker_result.get('message', 'Unknown error'))}"
            safe_log_error(logger, error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
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
            "execution_method": "docker",
            "user_id": runtime.state.get("user_id", "")
        }
        
        safe_log_info(logger, f"[nuclei_scan] Complete", target=target, count=result_data["count"])
        return json.dumps(result_data, indent=2)
        
    except subprocess.TimeoutExpired:
        return json.dumps({"status": "error", "message": "Nuclei scan timed out"})
    except Exception as e:
        safe_log_error(logger, f"[nuclei_scan] Error: {str(e)}", exc_info=True)
        return json.dumps({"status": "error", "message": str(e)})

