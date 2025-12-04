"""
zmap Tool for LangChain Agents

Single-packet scanning
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

logger = setup_logger(__name__, log_file_path="logs/zmap_tool.log")


class ZMapSecurityAgentState(AgentState):
    """Extended agent state for ZMap operations."""
    user_id: str = ""


def _check_zmap_installed() -> bool:
    """Check if ZMap binary/package is installed."""
    return shutil.which("zmap") is not None or True  # Adjust based on tool type


@tool
def zmap_scan(
    runtime: ToolRuntime,
    ip_range: str,
    port: int,
    bandwidth: str
) -> str:
    """
    Single-packet scanning
    
    Args:
        runtime: ToolRuntime instance (automatically injected).
                ip_range: str - Parameter description
        port: int - Parameter description
        bandwidth: str - Parameter description
    
    Returns:
        JSON string with results.
    """
    try:
        safe_log_info(logger, f"[zmap_scan] Starting", ip_range=ip_range, port=port, bandwidth=bandwidth)
        
        # Validate inputs
        if not ip_range or not isinstance(ip_range, str):
            error_msg = "Invalid IP range provided"
            safe_log_error(logger, error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        if not isinstance(port, int) or port < 1 or port > 65535:
            error_msg = "Port must be between 1 and 65535"
            safe_log_error(logger, error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        if not bandwidth or not isinstance(bandwidth, str):
            error_msg = "Invalid bandwidth provided"
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
            "port": port,
            "bandwidth": bandwidth,
            "user_id": runtime.state.get("user_id", "")
        }
        
        safe_log_info(logger, f"[zmap_scan] Complete", ip_range=ip_range, port=port)
        return json.dumps(result_data, indent=2)
        
    except Exception as e:
        safe_log_error(logger, f"[zmap_scan] Error: {str(e)}", exc_info=True)
        return json.dumps({"status": "error", "message": f"ZMap scan failed: {str(e)}"})
