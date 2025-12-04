"""
OnionSearch Tool for CrewAI Agents

Scrape Dark Web search engines
"""

import json
import subprocess
import shutil
from typing import Any, Optional, List
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error

logger = setup_logger(__name__, log_file_path="logs/onionsearch_tool.log")


class OnionSearchToolSchema(BaseModel):
    """Input schema for OnionSearchTool."""
    query: str = Field(..., description="Search query")
    engines: Optional[List[str]] = Field(default=None, description="Specific search engines")
    max_results: int = Field(default=50, ge=1, le=1000, description="Max results (1-1000)")


class OnionSearchTool(BaseTool):
    """Tool for Scrape Dark Web search engines."""
    
    name: str = "OnionSearch"
    description: str = "Scrape Dark Web search engines"
    args_schema: type[BaseModel] = OnionSearchToolSchema
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        # Add validation if needed
        # if not shutil.which("onionsearch"):
        #     raise ValueError("OnionSearch not found. Please install it.")
    
    def _run(
        self,
        query: str,
        engines: Optional[List[str]] = None,
        max_results: int = 50,
        **kwargs: Any
    ) -> str:
        """Execute OnionSearch dark web search."""
        try:
            safe_log_info(logger, f"[OnionSearchTool] Starting", query=query, engines=engines, max_results=max_results)
            
            # Validate inputs
            if not query or not isinstance(query, str) or len(query.strip()) == 0:
                error_msg = "Invalid query provided"
                safe_log_error(logger, error_msg)
                return json.dumps({"status": "error", "message": error_msg})
            
            if max_results < 1 or max_results > 1000:
                error_msg = "Max results must be between 1 and 1000"
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
                "query": query,
                "engines": engines or [],
                "max_results": max_results
            }
            
            safe_log_info(logger, f"[OnionSearchTool] Complete", query=query)
            return json.dumps(result_data, indent=2)
            
        except Exception as e:
            safe_log_error(logger, f"[OnionSearchTool] Error: {str(e)}", exc_info=True)
            return json.dumps({"status": "error", "message": f"OnionSearch failed: {str(e)}"})
