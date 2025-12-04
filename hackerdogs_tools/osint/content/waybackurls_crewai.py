"""
Waybackurls Tool for CrewAI Agents

Fetch URLs from Wayback Machine
"""

import json
import subprocess
import shutil
from typing import Any, Optional, List
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error

logger = setup_logger(__name__, log_file_path="logs/waybackurls_tool.log")


class WaybackurlsToolSchema(BaseModel):
    """Input schema for WaybackurlsTool."""
    domain: str = Field(..., description="Domain to fetch URLs for")
    no_subs: bool = Field(default=False, description="Exclude subdomains")
    dates: Optional[str] = Field(default=None, description="Date range (YYYYMMDD-YYYYMMDD)")


class WaybackurlsTool(BaseTool):
    """Tool for Fetch URLs from Wayback Machine."""
    
    name: str = "Waybackurls"
    description: str = "Fetch URLs from Wayback Machine"
    args_schema: type[BaseModel] = WaybackurlsToolSchema
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        # Add validation if needed
        # if not shutil.which("waybackurls"):
        #     raise ValueError("Waybackurls not found. Please install it.")
    
    def _run(
        self,
        domain: str,
        no_subs: bool = False,
        dates: Optional[str] = None,
        **kwargs: Any
    ) -> str:
        """Execute Waybackurls URL fetching."""
        try:
            safe_log_info(logger, f"[WaybackurlsTool] Starting", domain=domain, no_subs=no_subs, dates=dates)
            
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
                "domain": domain,
                "no_subs": no_subs,
                "dates": dates
            }
            
            safe_log_info(logger, f"[WaybackurlsTool] Complete", domain=domain)
            return json.dumps(result_data, indent=2)
            
        except Exception as e:
            safe_log_error(logger, f"[WaybackurlsTool] Error: {str(e)}", exc_info=True)
            return json.dumps({"status": "error", "message": f"Waybackurls failed: {str(e)}"})
