"""
Maigret Tool for CrewAI Agents

Advanced username search with metadata
"""

import json
import subprocess
import shutil
from typing import Any, Optional, List
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error

logger = setup_logger(__name__, log_file_path="logs/maigret_tool.log")


class MaigretToolSchema(BaseModel):
    """Input schema for MaigretTool."""
    username: str = Field(..., description="Username to search")
    extract_metadata: bool = Field(default=True, description="Extract metadata")
    sites: Optional[List[str]] = Field(default=None, description="Specific sites to search")


class MaigretTool(BaseTool):
    """Tool for Advanced username search with metadata."""
    
    name: str = "Maigret"
    description: str = "Advanced username search with metadata"
    args_schema: type[BaseModel] = MaigretToolSchema
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        # Add validation if needed
        # if not shutil.which("maigret"):
        #     raise ValueError("Maigret not found. Please install it.")
    
    def _run(
        self,
        username: str,
        extract_metadata: bool = True,
        sites: Optional[List[str]] = None,
        **kwargs: Any
    ) -> str:
        """Execute Maigret username search."""
        try:
            safe_log_info(logger, f"[MaigretTool] Starting", username=username, extract_metadata=extract_metadata, sites=sites)
            
            # Validate inputs
            if not username or not isinstance(username, str) or len(username.strip()) == 0:
                error_msg = "Invalid username provided"
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
                "extract_metadata": extract_metadata,
                "sites": sites or []
            }
            
            safe_log_info(logger, f"[MaigretTool] Complete", username=username)
            return json.dumps(result_data, indent=2)
            
        except Exception as e:
            safe_log_error(logger, f"[MaigretTool] Error: {str(e)}", exc_info=True)
            return json.dumps({"status": "error", "message": f"Maigret search failed: {str(e)}"})
