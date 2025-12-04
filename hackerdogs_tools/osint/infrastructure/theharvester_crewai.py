"""
TheHarvester Tool for CrewAI Agents

Gathers emails, subdomains, hosts from search engines
"""

import json
import subprocess
import shutil
from typing import Any, Optional, List
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error

logger = setup_logger(__name__, log_file_path="logs/theharvester_tool.log")


class TheHarvesterToolSchema(BaseModel):
    """Input schema for TheHarvesterTool."""
    domain: str = Field(..., description="Domain to search")
    sources: Optional[List[str]] = Field(default=None, description="Specific sources to use")
    limit: int = Field(default=500, ge=1, le=10000, description="Result limit (1-10000)")


class TheHarvesterTool(BaseTool):
    """Tool for Gathers emails, subdomains, hosts from search engines."""
    
    name: str = "TheHarvester"
    description: str = "Gathers emails, subdomains, hosts from search engines"
    args_schema: type[BaseModel] = TheHarvesterToolSchema
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        # Add validation if needed
        # if not shutil.which("theharvester"):
        #     raise ValueError("TheHarvester not found. Please install it.")
    
    def _run(
        self,
        domain: str,
        sources: Optional[List[str]] = None,
        limit: int = 500,
        **kwargs: Any
    ) -> str:
        """Execute TheHarvester information gathering."""
        try:
            safe_log_info(logger, f"[TheHarvesterTool] Starting", domain=domain, sources=sources, limit=limit)
            
            # Validate inputs
            if not domain or not isinstance(domain, str) or len(domain.strip()) == 0:
                error_msg = "Invalid domain provided"
                safe_log_error(logger, error_msg)
                return json.dumps({"status": "error", "message": error_msg})
            
            if limit < 1 or limit > 10000:
                error_msg = "Limit must be between 1 and 10000"
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
                "sources": sources or [],
                "limit": limit
            }
            
            safe_log_info(logger, f"[TheHarvesterTool] Complete", domain=domain)
            return json.dumps(result_data, indent=2)
            
        except Exception as e:
            safe_log_error(logger, f"[TheHarvesterTool] Error: {str(e)}", exc_info=True)
            return json.dumps({"status": "error", "message": f"TheHarvester search failed: {str(e)}"})
