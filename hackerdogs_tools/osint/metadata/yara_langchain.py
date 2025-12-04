"""
yara Tool for LangChain Agents

Pattern matching for malware classification
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

logger = setup_logger(__name__, log_file_path="logs/yara_tool.log")


class YARASecurityAgentState(AgentState):
    """Extended agent state for YARA operations."""
    user_id: str = ""


def _check_yara_installed() -> bool:
    """Check if YARA binary/package is installed."""
    return shutil.which("yara") is not None or True  # Adjust based on tool type


@tool
def yara_search(
    runtime: ToolRuntime,
    file_path: str,
    rules_path: str,
    rules_content: Optional[str] = None
) -> str:
    """
    Pattern matching for malware classification
    
    Args:
        runtime: ToolRuntime instance (automatically injected).
                file_path: str - Parameter description
        rules_path: str - Parameter description
        rules_content: str - Parameter description
    
    Returns:
        JSON string with results.
    """
    try:
        safe_log_info(logger, f"[yara_search] Starting", file_path=file_path, rules_path=rules_path, rules_content=rules_content)
        
        # Validate inputs
        if not file_path or not isinstance(file_path, str):
            error_msg = "Invalid file_path provided"
            safe_log_error(logger, error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        if not rules_path and not rules_content:
            error_msg = "Either rules_path or rules_content must be provided"
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
            "file_path": file_path,
            "rules_path": rules_path,
            "user_id": runtime.state.get("user_id", "")
        }
        
        safe_log_info(logger, f"[yara_search] Complete", file_path=file_path)
        return json.dumps(result_data, indent=2)
        
    except Exception as e:
        safe_log_error(logger, f"[yara_search] Error: {str(e)}", exc_info=True)
        return json.dumps({"status": "error", "message": f"YARA search failed: {str(e)}"})
