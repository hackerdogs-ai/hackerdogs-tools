"""
Subfinder Tool for CrewAI Agents

Fast passive subdomain discovery using ProjectDiscovery Subfinder.
"""

import json
import subprocess
import shutil
from typing import Any
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error
from hackerdogs_tools.osint.docker_client import get_docker_client, execute_in_docker

logger = setup_logger(__name__, log_file_path="logs/subfinder_tool.log")


class SubfinderToolSchema(BaseModel):
    """Input schema for SubfinderTool."""
    domain: str = Field(..., description="Target domain to enumerate")
    recursive: bool = Field(default=False, description="Recursive enumeration")
    silent: bool = Field(default=True, description="Silent mode")


class SubfinderTool(BaseTool):
    """Tool for fast passive subdomain discovery using Subfinder."""
    
    name: str = "Subfinder Subdomain Discovery"
    description: str = (
        "Fast passive subdomain discovery using Subfinder. "
        "Use this for quick subdomain enumeration from passive sources."
    )
    args_schema: type[BaseModel] = SubfinderToolSchema
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        # Docker-only - no host binaries allowed
        docker_client = get_docker_client()
        if not docker_client or not docker_client.docker_available:
            raise ValueError(
                "Docker is required for OSINT tools. Setup:\n"
                "1. Build Docker image: cd hackerdogs_tools/osint/docker && docker build -t osint-tools:latest .\n"
                "2. Start container: docker-compose up -d"
            )
    
    def _run(self, domain: str, recursive: bool = False, silent: bool = True, **kwargs: Any) -> str:
        """Execute Subfinder enumeration in Docker container."""
        try:
            safe_log_info(logger, f"[SubfinderTool] Starting", domain=domain)
            
            args = ["-d", domain, "-oJ", "-"]
            if recursive:
                args.append("-recursive")
            if silent:
                args.append("-silent")
            
            # Execute in Docker
            docker_result = execute_in_docker("subfinder", args, timeout=300)
            
            if docker_result["status"] != "success":
                return json.dumps({
                    "status": "error",
                    "message": docker_result.get("stderr", docker_result.get("message", "Unknown error"))
                })
            
            subdomains = []
            stdout = docker_result.get("stdout", "")
            for line in stdout.strip().split('\n'):
                if line.strip():
                    try:
                        data = json.loads(line)
                        if 'host' in data:
                            subdomains.append(data['host'])
                    except json.JSONDecodeError:
                        continue
            
            result_data = {
                "status": "success",
                "domain": domain,
                "subdomains": list(set(subdomains)),
                "count": len(set(subdomains)),
                "execution_method": docker_result.get("execution_method", "docker")
            }
            
            return json.dumps(result_data, indent=2)
            
        except Exception as e:
            safe_log_error(logger, f"[SubfinderTool] Error: {str(e)}", exc_info=True)
            return json.dumps({"status": "error", "message": str(e)})

