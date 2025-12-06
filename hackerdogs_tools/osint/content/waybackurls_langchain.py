"""
waybackurls Tool for LangChain Agents

Fetch URLs from Wayback Machine
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

logger = setup_logger(__name__, log_file_path="logs/waybackurls_tool.log")


class WaybackurlsSecurityAgentState(AgentState):
    """Extended agent state for Waybackurls operations."""
    user_id: str = ""


def _check_waybackurls_installed() -> bool:
    """Check if Waybackurls binary/package is installed."""
    return shutil.which("waybackurls") is not None or True  # Adjust based on tool type


@tool
def waybackurls_search(
    runtime: ToolRuntime,
    domain: str,
    no_subs: bool = False,
    dates: Optional[str] = None
) -> str:
    """
    Fetch URLs from Wayback Machine
    
    Args:
        runtime: ToolRuntime instance (automatically injected).
                domain: str - Parameter description
        no_subs: bool - Parameter description
        dates: str - Parameter description
    
    Returns:
        JSON string with results.
    """
    try:
        safe_log_info(logger, f"[waybackurls_search] Starting", domain=domain, no_subs=no_subs, dates=dates)
        
        # Validate inputs
        if not domain or not isinstance(domain, str) or len(domain.strip()) == 0:
            error_msg = "Invalid domain provided"
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
        
        safe_log_info(logger, f"[waybackurls_search] Complete", domain=domain)
        return json.dumps({"status": "error", "message": "Tool execution not yet implemented"})
        
    except Exception as e:
        safe_log_error(logger, f"[waybackurls_search] Error: {str(e)}", exc_info=True)
        return json.dumps({"status": "error", "message": f"Waybackurls search failed: {str(e)}"})
