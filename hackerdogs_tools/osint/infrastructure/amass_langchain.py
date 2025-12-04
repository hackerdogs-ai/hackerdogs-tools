"""
OWASP Amass Tool for LangChain Agents

This module provides LangChain tools for subdomain enumeration using OWASP Amass.
Amass is the gold standard for subdomain enumeration and asset mapping.

Reference: https://github.com/OWASP/Amass
"""

import json
import subprocess
import shutil
from typing import Optional, Dict, Any
from langchain.tools import tool, ToolRuntime
from langchain.agents import AgentState
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import (
    safe_log_debug,
    safe_log_info,
    safe_log_error
)
from hackerdogs_tools.osint.docker_client import get_docker_client, execute_in_docker

logger = setup_logger(__name__, log_file_path="logs/amass_tool.log")


class AmassSecurityAgentState(AgentState):
    """Extended agent state for Amass operations."""
    user_id: str = ""
    api_keys: Dict[str, str] = {}


def _check_docker_available() -> bool:
    """Check if Docker is available for running Amass in container."""
    client = get_docker_client()
    return client is not None and client.docker_available


@tool
def amass_enum(
    runtime: ToolRuntime,
    domain: str,
    passive: bool = False,
    active: bool = True,
    timeout: int = 300
) -> str:
    """
    Enumerate subdomains for a domain using OWASP Amass.
    
    This tool uses OWASP Amass to perform comprehensive subdomain enumeration
    and asset mapping. Amass combines multiple data sources including passive
    DNS, certificate transparency logs, and active enumeration techniques.
    
    When to use:
        - User asks to find all subdomains for a domain
        - Need comprehensive subdomain enumeration
        - Mapping attack surface for a target domain
        - Security assessment: discovering all assets
    
    When NOT to use:
        - Need fast, lightweight enumeration (use Subfinder instead)
        - Domain format is invalid
        - Timeout is too short for large domains
    
    Args:
        runtime: ToolRuntime instance (automatically injected).
        domain: Target domain (e.g., "tesla.com").
        passive: Use passive enumeration only (default: False).
        active: Use active enumeration (default: True).
        timeout: Timeout in seconds (default: 300).
    
    Returns:
        JSON string with subdomains, IPs, and network graph.
    """
    try:
        safe_log_info(logger, f"[amass_enum] Starting enumeration", domain=domain)
        
        # Docker-only execution - no host binaries allowed
        if not _check_docker_available():
            error_msg = (
                "Docker is required for OSINT tools. Setup:\n"
                "1. Build Docker image: cd hackerdogs_tools/osint/docker && docker build -t osint-tools:latest .\n"
                "2. Start container: docker-compose up -d\n"
                "3. Ensure Docker is running: docker ps"
            )
            safe_log_error(logger, error_msg)
            return json.dumps({
                "status": "error",
                "message": error_msg
            })
        
        # Build Amass command arguments
        args = []
        if passive:
            args.append("-passive")
        if active:
            args.append("-active")
        args.extend(["-d", domain, "-json", "-o", "-"])
        
        # Execute in Docker container
        safe_log_debug(logger, "[amass_enum] Executing in Docker container")
        docker_result = execute_in_docker("amass", ["enum"] + args, timeout=timeout)
        
        if docker_result["status"] != "success":
            error_msg = f"Amass enumeration failed: {docker_result.get('stderr', docker_result.get('message', 'Unknown error'))}"
            safe_log_error(logger, error_msg)
            return json.dumps({
                "status": "error",
                "message": error_msg
            })
        
        stdout = docker_result.get("stdout", "")
        
        # Parse JSON output (one JSON object per line)
        subdomains = []
        ips = []
        for line in stdout.strip().split('\n'):
            if not line.strip():
                continue
            try:
                data = json.loads(line)
                if 'name' in data:
                    subdomains.append(data['name'])
                if 'addresses' in data:
                    for addr in data['addresses']:
                        if 'ip' in addr:
                            ips.append(addr['ip'])
            except json.JSONDecodeError:
                continue
        
        result_data = {
            "status": "success",
            "domain": domain,
            "subdomains": list(set(subdomains)),
            "ip_addresses": list(set(ips)),
            "subdomain_count": len(set(subdomains)),
            "ip_count": len(set(ips)),
            "execution_method": "docker",
            "user_id": runtime.state.get("user_id", "")
        }
        
        safe_log_info(logger, f"[amass_enum] Enumeration complete", 
                     domain=domain, subdomain_count=result_data["subdomain_count"])
        
        return json.dumps(result_data, indent=2)
        
    except subprocess.TimeoutExpired:
        error_msg = f"Amass enumeration timed out after {timeout} seconds"
        safe_log_error(logger, error_msg)
        return json.dumps({
            "status": "error",
            "message": error_msg
        })
    except Exception as e:
        error_msg = f"Unexpected error running Amass: {str(e)}"
        safe_log_error(logger, error_msg, exc_info=True)
        return json.dumps({
            "status": "error",
            "message": error_msg
        })

