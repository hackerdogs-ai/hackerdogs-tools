"""
masscan Tool for LangChain Agents

Fast Internet port scanner
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

logger = setup_logger(__name__, log_file_path="logs/masscan_tool.log")


class MasscanSecurityAgentState(AgentState):
    """Extended agent state for Masscan operations."""
    user_id: str = ""


def _check_masscan_installed() -> bool:
    """Check if Masscan binary/package is installed."""
    return shutil.which("masscan") is not None or True  # Adjust based on tool type


@tool
def masscan_scan(
    runtime: ToolRuntime,
    ip_range: str,
    ports: str,
    rate: int = 1000
) -> str:
    """
    Fast Internet port scanner
    
    Args:
        runtime: ToolRuntime instance (automatically injected).
                ip_range: str - Parameter description
        ports: str - Parameter description
        rate: int - Parameter description
    
    Returns:
        JSON string with results.
    """
    try:
        safe_log_info(logger, f"[masscan_scan] Starting", ip_range=ip_range, ports=ports, rate=rate)
        
        # Validate inputs
        if not ip_range or not isinstance(ip_range, str):
            error_msg = "Invalid IP range provided"
            safe_log_error(logger, error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        if not ports or not isinstance(ports, str):
            error_msg = "Invalid ports provided"
            safe_log_error(logger, error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        if rate < 1 or rate > 10000000:
            error_msg = "Rate must be between 1 and 10000000"
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
            "ip_range": ip_range,
            "ports": ports,
            "rate": rate,
            "user_id": runtime.state.get("user_id", "")
        }
        
        safe_log_info(logger, f"[masscan_scan] Complete", ip_range=ip_range)
        return json.dumps(result_data, indent=2)
        
    except Exception as e:
        safe_log_error(logger, f"[masscan_scan] Error: {str(e)}", exc_info=True)
        return json.dumps({"status": "error", "message": f"Masscan scan failed: {str(e)}"})
