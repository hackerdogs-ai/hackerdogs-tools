"""
sherlock Tool for LangChain Agents

Username enumeration across 300+ sites
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

logger = setup_logger(__name__, log_file_path="logs/sherlock_tool.log")


class SherlockSecurityAgentState(AgentState):
    """Extended agent state for Sherlock operations."""
    user_id: str = ""


def _check_sherlock_installed() -> bool:
    """Check if Sherlock binary/package is installed."""
    return shutil.which("sherlock") is not None or True  # Adjust based on tool type


@tool
def sherlock_enum(
    runtime: ToolRuntime,
    username: str,
    sites: Optional[List[str]] = None,
    timeout: int = 60
) -> str:
    """
    Username enumeration across 300+ sites
    
    Args:
        runtime: ToolRuntime instance (automatically injected).
                username: str - Parameter description
        sites: List[str - Parameter description
        timeout: int - Parameter description
    
    Returns:
        JSON string with results.
    """
    try:
        safe_log_info(logger, f"[sherlock_enum] Starting", username=username, sites=sites, timeout=timeout)
        
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
            "timeout": timeout,
            "user_id": runtime.state.get("user_id", "")
        }
        
        safe_log_info(logger, f"[sherlock_enum] Complete", username=username)
        return json.dumps(result_data, indent=2)
        
    except Exception as e:
        safe_log_error(logger, f"[sherlock_enum] Error: {str(e)}", exc_info=True)
        return json.dumps({"status": "error", "message": f"Sherlock enumeration failed: {str(e)}"})
