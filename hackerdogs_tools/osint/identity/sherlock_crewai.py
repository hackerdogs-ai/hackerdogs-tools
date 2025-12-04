"""
Sherlock Tool for CrewAI Agents

Username enumeration across 300+ sites
"""

import json
import subprocess
import shutil
from typing import Any, Optional, List
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error

logger = setup_logger(__name__, log_file_path="logs/sherlock_tool.log")


class SherlockToolSchema(BaseModel):
    """Input schema for SherlockTool."""
    username: str = Field(..., description="Username to search")
    sites: Optional[List[str]] = Field(default=None, description="Specific sites to search")
    timeout: int = Field(default=60, ge=1, le=3600, description="Timeout in seconds (1-3600)")


class SherlockTool(BaseTool):
    """Tool for Username enumeration across 300+ sites."""
    
    name: str = "Sherlock"
    description: str = "Username enumeration across 300+ sites"
    args_schema: type[BaseModel] = SherlockToolSchema
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        # Add validation if needed
        # if not shutil.which("sherlock"):
        #     raise ValueError("Sherlock not found. Please install it.")
    
    def _run(
        self,
        username: str,
        sites: Optional[List[str]] = None,
        timeout: int = 60,
        **kwargs: Any
    ) -> str:
        """Execute Sherlock username enumeration."""
        try:
            safe_log_info(logger, f"[SherlockTool] Starting", username=username, sites=sites, timeout=timeout)
            
            # Validate inputs
            if not username or not isinstance(username, str) or len(username.strip()) == 0:
                error_msg = "Invalid username provided"
                safe_log_error(logger, error_msg)
                return json.dumps({"status": "error", "message": error_msg})
            
            if timeout < 1 or timeout > 3600:
                error_msg = "Timeout must be between 1 and 3600 seconds"
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
                "username": username,
                "sites": sites or [],
                "timeout": timeout
            }
            
            safe_log_info(logger, f"[SherlockTool] Complete", username=username)
            return json.dumps(result_data, indent=2)
            
        except Exception as e:
            safe_log_error(logger, f"[SherlockTool] Error: {str(e)}", exc_info=True)
            return json.dumps({"status": "error", "message": f"Sherlock enumeration failed: {str(e)}"})
