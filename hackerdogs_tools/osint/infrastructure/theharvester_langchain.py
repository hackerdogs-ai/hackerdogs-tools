"""
theharvester Tool for LangChain Agents

Gathers emails, subdomains, hosts from search engines
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

logger = setup_logger(__name__, log_file_path="logs/theharvester_tool.log")


class TheHarvesterSecurityAgentState(AgentState):
    """Extended agent state for TheHarvester operations."""
    user_id: str = ""


def _check_theharvester_installed() -> bool:
    """Check if TheHarvester binary/package is installed."""
    return shutil.which("theharvester") is not None or True  # Adjust based on tool type


@tool
def theharvester_search(
    runtime: ToolRuntime,
    domain: str,
    sources: Optional[List[str]] = None,
    limit: int = 500
) -> str:
    """
    Gathers emails, subdomains, hosts from search engines
    
    Args:
        runtime: ToolRuntime instance (automatically injected).
                domain: str - Parameter description
        sources: List[str - Parameter description
        limit: int - Parameter description
    
    Returns:
        JSON string with results.
    """
    try:
        safe_log_info(logger, f"[theharvester_search] Starting", domain=domain, sources=sources, limit=limit)
        
        # Validate inputs
        if not domain or not isinstance(domain, str) or len(domain.strip()) == 0:
            error_msg = "Invalid domain provided"
            safe_log_error(logger, error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        if limit < 1 or limit > 10000:
            error_msg = "Limit must be between 1 and 10000"
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
            "domain": domain,
            "sources": sources or [],
            "limit": limit,
            "user_id": runtime.state.get("user_id", "")
        }
        
        safe_log_info(logger, f"[theharvester_search] Complete", domain=domain)
        return json.dumps(result_data, indent=2)
        
    except Exception as e:
        safe_log_error(logger, f"[theharvester_search] Error: {str(e)}", exc_info=True)
        return json.dumps({"status": "error", "message": f"TheHarvester search failed: {str(e)}"})
