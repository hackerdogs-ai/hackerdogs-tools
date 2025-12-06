"""
abuseipdb Tool for LangChain Agents

IP reputation and abuse checking
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

logger = setup_logger(__name__, log_file_path="logs/abuseipdb_tool.log")


class AbuseIPDBSecurityAgentState(AgentState):
    """Extended agent state for AbuseIPDB operations."""
    user_id: str = ""


def _check_abuseipdb_installed() -> bool:
    """Check if AbuseIPDB binary/package is installed."""
    return shutil.which("abuseipdb") is not None or True  # Adjust based on tool type


@tool
def abuseipdb_search(
    runtime: ToolRuntime,
    ip: str,
    max_age_in_days: int = 90,
    verbose: bool = True
) -> str:
    """
    IP reputation and abuse checking
    
    Args:
        runtime: ToolRuntime instance (automatically injected).
                ip: str - Parameter description
        max_age_in_days: int - Parameter description
        verbose: bool - Parameter description
    
    Returns:
        JSON string with results.
    """
    try:
        safe_log_info(logger, f"[abuseipdb_search] Starting", ip=ip, max_age_in_days=max_age_in_days, verbose=verbose)
        
        # Validate inputs
        if not ip or not isinstance(ip, str):
            error_msg = "Invalid IP address provided"
            safe_log_error(logger, error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        if max_age_in_days < 1 or max_age_in_days > 365:
            error_msg = "Max age must be between 1 and 365 days"
            safe_log_error(logger, error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        # Note: AbuseIPDB is an API service, not a binary tool
        # This would use API calls, not Docker
        
        # TODO: Implement tool-specific logic
        # This is a template - implement actual tool execution
        
        safe_log_info(logger, f"[abuseipdb_search] Complete", ip=ip)
        return json.dumps({"status": "error", "message": "Tool execution not yet implemented"})
        
    except Exception as e:
        safe_log_error(logger, f"[abuseipdb_search] Error: {str(e)}", exc_info=True)
        return json.dumps({"status": "error", "message": f"AbuseIPDB check failed: {str(e)}"})
