"""
DNSDumpster Tool for CrewAI Agents

DNS mapping via DNSDumpster
"""

import json
import subprocess
import shutil
from typing import Any, Optional, List
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error

logger = setup_logger(__name__, log_file_path="logs/dnsdumpster_tool.log")


class DNSDumpsterToolSchema(BaseModel):
    """Input schema for DNSDumpsterTool."""
    domain: str = Field(..., description="Domain to map DNS records for")


class DNSDumpsterTool(BaseTool):
    """Tool for DNS mapping via DNSDumpster."""
    
    name: str = "DNSDumpster"
    description: str = "DNS mapping via DNSDumpster"
    args_schema: type[BaseModel] = DNSDumpsterToolSchema
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        # Add validation if needed
        # if not shutil.which("dnsdumpster"):
        #     raise ValueError("DNSDumpster not found. Please install it.")
    
    def _run(
        self,
        domain: str,
        **kwargs: Any
    ) -> str:
        """Execute DNSDumpster DNS mapping."""
        try:
            safe_log_info(logger, f"[DNSDumpsterTool] Starting", domain=domain)
            
            # Validate inputs
            if not domain or not isinstance(domain, str) or len(domain.strip()) == 0:
                error_msg = "Invalid domain provided"
                safe_log_error(logger, error_msg)
                return json.dumps({"status": "error", "message": error_msg})
            
            # Check Docker availability (Docker-only execution)
            from hackerdogs_tools.osint.docker_client import get_docker_client, execute_in_docker
            docker_client = get_docker_client()
            
            if not docker_client or not docker_client.docker_available:
                error_msg = (
                    "Docker is required for OSINT tools. Setup:\n"
                    "1. Build Docker image: cd hackerdogs_tools/osint/docker && docker build -t osint-tools:latest .\n"
                    "2. Start container: docker-compose up -d"
                )
                safe_log_error(logger, error_msg)
                return json.dumps({"status": "error", "message": error_msg})
            
            # TODO: Implement tool-specific logic
            # This is a template - implement actual tool execution
            
            result_data = {
                "status": "success",
                "message": "Tool execution not yet implemented",
                "domain": domain
            }
            
            safe_log_info(logger, f"[DNSDumpsterTool] Complete", domain=domain)
            return json.dumps(result_data, indent=2)
            
        except Exception as e:
            safe_log_error(logger, f"[DNSDumpsterTool] Error: {str(e)}", exc_info=True)
            return json.dumps({"status": "error", "message": f"DNSDumpster search failed: {str(e)}"})
