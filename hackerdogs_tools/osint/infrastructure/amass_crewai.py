"""
OWASP Amass Tool for CrewAI Agents

This module provides CrewAI tools for subdomain enumeration using OWASP Amass.
"""

import json
import subprocess
import shutil
import os
from typing import Any
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import (
    safe_log_debug,
    safe_log_info,
    safe_log_error
)
from hackerdogs_tools.osint.docker_client import get_docker_client, execute_in_docker

logger = setup_logger(__name__, log_file_path="logs/amass_tool.log")


class AmassToolSchema(BaseModel):
    """Input schema for AmassTool."""
    domain: str = Field(..., description="Target domain to enumerate (e.g., 'tesla.com')")
    passive: bool = Field(default=False, description="Use passive enumeration only")
    active: bool = Field(default=True, description="Use active enumeration")
    timeout: int = Field(default=300, ge=60, le=3600, description="Timeout in seconds (60-3600)")


class AmassTool(BaseTool):
    """Tool for subdomain enumeration using OWASP Amass."""
    
    name: str = "Amass Subdomain Enumeration"
    description: str = (
        "Enumerate subdomains for a domain using OWASP Amass. "
        "Provides comprehensive subdomain discovery and asset mapping. "
        "Use this for thorough subdomain enumeration and attack surface mapping."
    )
    args_schema: type[BaseModel] = AmassToolSchema
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        # Docker-only - no host binaries allowed
        docker_client = get_docker_client()
        if not docker_client or not docker_client.docker_available:
            raise ValueError(
                "Docker is required for OSINT tools. Setup:\n"
                "1. Build Docker image: cd hackerdogs_tools/osint/docker && docker build -t osint-tools:latest .\n"
                "2. Start container: docker-compose up -d\n"
                "3. Ensure Docker is running: docker ps"
            )
    
    def _run(
        self,
        domain: str,
        passive: bool = False,
        active: bool = True,
        timeout: int = 300,
        **kwargs: Any
    ) -> str:
        """Execute Amass enumeration in Docker container."""
        try:
            safe_log_info(logger, f"[AmassTool] Starting enumeration", domain=domain)
            
            # Docker-only execution
            # Build arguments
            args = []
            if passive:
                args.append("-passive")
            if active:
                args.append("-active")
            args.extend(["-d", domain, "-json", "-o", "-"])
            
            # Execute in Docker container
            safe_log_debug(logger, "[AmassTool] Executing in Docker container")
            docker_result = execute_in_docker("amass", ["enum"] + args, timeout=timeout)
            
            if docker_result["status"] != "success":
                error_msg = docker_result.get("stderr", docker_result.get("message", "Unknown error"))
                safe_log_error(logger, f"[AmassTool] Docker execution failed: {error_msg}")
                return json.dumps({
                    "status": "error",
                    "message": f"Amass enumeration failed: {error_msg}"
                })
            
            stdout = docker_result.get("stdout", "")
            
            # Parse JSON output
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
                "execution_method": "docker"
            }
            
            safe_log_info(logger, f"[AmassTool] Enumeration complete", 
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

