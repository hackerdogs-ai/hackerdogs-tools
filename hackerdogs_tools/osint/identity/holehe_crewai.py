"""
Holehe Tool for CrewAI Agents

Check email registration on 120+ sites
"""

import json
import subprocess
import shutil
from typing import Any, Optional, List
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error

logger = setup_logger(__name__, log_file_path="logs/holehe_tool.log")


class HoleheToolSchema(BaseModel):
    """Input schema for HoleheTool."""
    email: str = Field(..., description="Email address to check")
    only_used: bool = Field(default=True, description="Only show sites where email is used")


class HoleheTool(BaseTool):
    """Tool for Check email registration on 120+ sites."""
    
    name: str = "Holehe"
    description: str = "Check email registration on 120+ sites"
    args_schema: type[BaseModel] = HoleheToolSchema
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        # Add validation if needed
        # if not shutil.which("holehe"):
        #     raise ValueError("Holehe not found. Please install it.")
    
    def _run(
        self,
        email: str,
        only_used: bool = True,
        **kwargs: Any
    ) -> str:
        """Execute Holehe email check."""
        try:
            safe_log_info(logger, f"[HoleheTool] Starting", email=email, only_used=only_used)
            
            # Validate inputs
            if not email or not isinstance(email, str) or "@" not in email:
                error_msg = "Invalid email address provided"
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
                "email": email,
                "only_used": only_used
            }
            
            safe_log_info(logger, f"[HoleheTool] Complete", email=email)
            return json.dumps(result_data, indent=2)
            
        except Exception as e:
            safe_log_error(logger, f"[HoleheTool] Error: {str(e)}", exc_info=True)
            return json.dumps({"status": "error", "message": f"Holehe check failed: {str(e)}"})
