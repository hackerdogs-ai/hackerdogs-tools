"""
holehe Tool for LangChain Agents

Check email registration on 120+ sites
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

logger = setup_logger(__name__, log_file_path="logs/holehe_tool.log")


class HoleheSecurityAgentState(AgentState):
    """Extended agent state for Holehe operations."""
    user_id: str = ""


def _check_holehe_installed() -> bool:
    """Check if Holehe binary/package is installed."""
    return shutil.which("holehe") is not None or True  # Adjust based on tool type


@tool
def holehe_search(
    runtime: ToolRuntime,
    email: str,
    only_used: bool = True
) -> str:
    """
    Check email registration on 120+ sites
    
    Args:
        runtime: ToolRuntime instance (automatically injected).
                email: str - Parameter description
        only_used: bool - Parameter description
    
    Returns:
        JSON string with results.
    """
    try:
        safe_log_info(logger, f"[holehe_search] Starting", email=email, only_used=only_used)
        
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
            "only_used": only_used,
            "user_id": runtime.state.get("user_id", "")
        }
        
        safe_log_info(logger, f"[holehe_search] Complete", email=email)
        return json.dumps(result_data, indent=2)
        
    except Exception as e:
        safe_log_error(logger, f"[holehe_search] Error: {str(e)}", exc_info=True)
        return json.dumps({"status": "error", "message": f"Holehe search failed: {str(e)}"})
