"""
exiftool Tool for LangChain Agents

Extract metadata from images/PDFs
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

logger = setup_logger(__name__, log_file_path="logs/exiftool_tool.log")


class ExifToolSecurityAgentState(AgentState):
    """Extended agent state for ExifTool operations."""
    user_id: str = ""


def _check_exiftool_installed() -> bool:
    """Check if ExifTool binary/package is installed."""
    return shutil.which("exiftool") is not None or True  # Adjust based on tool type


@tool
def exiftool_search(
    runtime: ToolRuntime,
    file_path: str,
    extract_gps: bool = True,
    extract_author: bool = True
) -> str:
    """
    Extract metadata from images/PDFs
    
    Args:
        runtime: ToolRuntime instance (automatically injected).
                file_path: str - Parameter description
        extract_gps: bool - Parameter description
        extract_author: bool - Parameter description
    
    Returns:
        JSON string with results.
    """
    try:
        safe_log_info(logger, f"[exiftool_search] Starting", file_path=file_path, extract_gps=extract_gps, extract_author=extract_author)
        
        # Validate inputs
        if not file_path or not isinstance(file_path, str):
            error_msg = "Invalid file_path provided"
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
        
        safe_log_info(logger, f"[exiftool_search] Complete", file_path=file_path)
        return json.dumps({"status": "error", "message": "Tool execution not yet implemented"})
        
    except Exception as e:
        safe_log_error(logger, f"[exiftool_search] Error: {str(e)}", exc_info=True)
        return json.dumps({"status": "error", "message": f"ExifTool search failed: {str(e)}"})
