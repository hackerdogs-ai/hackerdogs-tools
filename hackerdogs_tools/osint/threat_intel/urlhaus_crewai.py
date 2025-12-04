"""
URLHaus Tool for CrewAI Agents

Check if URL is in malicious database
"""

import json
import subprocess
import shutil
from typing import Any, Optional, List
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error

logger = setup_logger(__name__, log_file_path="logs/urlhaus_tool.log")


class URLHausToolSchema(BaseModel):
    """Input schema for URLHausTool."""
    url: str = Field(..., description="URL to check in malicious database")
    download_feed: bool = Field(default=False, description="Download full feed")


class URLHausTool(BaseTool):
    """Tool for Check if URL is in malicious database."""
    
    name: str = "URLHaus"
    description: str = "Check if URL is in malicious database"
    args_schema: type[BaseModel] = URLHausToolSchema
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        # Add validation if needed
        # if not shutil.which("urlhaus"):
        #     raise ValueError("URLHaus not found. Please install it.")
    
    def _run(
        self,
        url: str,
        download_feed: bool = False,
        **kwargs: Any
    ) -> str:
        """Execute URLHaus URL check."""
        try:
            safe_log_info(logger, f"[URLHausTool] Starting", url=url, download_feed=download_feed)
            
            # Validate inputs
            if not url or not isinstance(url, str) or not url.startswith(("http://", "https://")):
                error_msg = "Invalid URL provided (must start with http:// or https://)"
                safe_log_error(logger, error_msg)
                return json.dumps({"status": "error", "message": error_msg})
            
            # Note: URLHaus is an API service, not a binary tool
            # This would use API calls, not Docker
            
            # TODO: Implement tool-specific logic
            # This is a template - implement actual tool execution
            
            result_data = {
                "status": "success",
                "message": "Tool execution not yet implemented",
                "url": url,
                "download_feed": download_feed
            }
            
            safe_log_info(logger, f"[URLHausTool] Complete", url=url)
            return json.dumps(result_data, indent=2)
            
        except Exception as e:
            safe_log_error(logger, f"[URLHausTool] Error: {str(e)}", exc_info=True)
            return json.dumps({"status": "error", "message": f"URLHaus check failed: {str(e)}"})
