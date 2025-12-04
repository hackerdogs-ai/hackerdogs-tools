"""
urlhaus Tool for LangChain Agents

Check if URL is in malicious database
"""

import json
import subprocess
import shutil
from typing import Optional, List
from langchain.tools import tool, ToolRuntime
from langchain.agents import AgentState
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error

logger = setup_logger(__name__, log_file_path="logs/urlhaus_tool.log")


class URLHausSecurityAgentState(AgentState):
    """Extended agent state for URLHaus operations."""
    user_id: str = ""


def _check_urlhaus_installed() -> bool:
    """Check if URLHaus binary/package is installed."""
    return shutil.which("urlhaus") is not None or True  # Adjust based on tool type


@tool
def urlhaus_search(
    runtime: ToolRuntime,
    url: str,
    download_feed: bool = False
) -> str:
    """
    Check if URL is in malicious database
    
    Args:
        runtime: ToolRuntime instance (automatically injected).
                url: str - Parameter description
        download_feed: bool - Parameter description
    
    Returns:
        JSON string with results.
    """
    try:
        safe_log_info(logger, f"[urlhaus_search] Starting", url=url, download_feed=download_feed)
        
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
            "download_feed": download_feed,
            "user_id": runtime.state.get("user_id", "")
        }
        
        safe_log_info(logger, f"[urlhaus_search] Complete", url=url)
        return json.dumps(result_data, indent=2)
        
    except Exception as e:
        safe_log_error(logger, f"[urlhaus_search] Error: {str(e)}", exc_info=True)
        return json.dumps({"status": "error", "message": f"URLHaus check failed: {str(e)}"})
