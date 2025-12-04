"""
spiderfoot Tool for LangChain Agents

Comprehensive OSINT framework
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

logger = setup_logger(__name__, log_file_path="logs/spiderfoot_tool.log")


class SpiderFootSecurityAgentState(AgentState):
    """Extended agent state for SpiderFoot operations."""
    user_id: str = ""


def _check_spiderfoot_installed() -> bool:
    """Check if SpiderFoot binary/package is installed."""
    return shutil.which("spiderfoot") is not None or True  # Adjust based on tool type


@tool
def spiderfoot_search(
    runtime: ToolRuntime,
    target: str,
    target_type: str,
    modules: Optional[List[str]] = None,
    scan_type: str = "footprint"
) -> str:
    """
    Comprehensive OSINT framework
    
    Args:
        runtime: ToolRuntime instance (automatically injected).
                target: str - Parameter description
        target_type: str - Parameter description
        modules: List[str - Parameter description
        scan_type: str - Parameter description
    
    Returns:
        JSON string with results.
    """
    try:
        safe_log_info(logger, f"[spiderfoot_search] Starting", target=target, target_type=target_type, modules=modules, scan_type=scan_type)
        
        # Validate inputs
        if not target or not isinstance(target, str) or len(target.strip()) == 0:
            error_msg = "Invalid target provided"
            safe_log_error(logger, error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        if target_type not in ["ip", "domain", "url", "email", "phone"]:
            error_msg = "Invalid target_type. Must be: ip, domain, url, email, or phone"
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
            "target": target,
            "target_type": target_type,
            "modules": modules or [],
            "scan_type": scan_type,
            "user_id": runtime.state.get("user_id", "")
        }
        
        safe_log_info(logger, f"[spiderfoot_search] Complete", target=target)
        return json.dumps(result_data, indent=2)
        
    except Exception as e:
        safe_log_error(logger, f"[spiderfoot_search] Error: {str(e)}", exc_info=True)
        return json.dumps({"status": "error", "message": f"SpiderFoot search failed: {str(e)}"})
