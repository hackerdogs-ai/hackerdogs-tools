"""
scrapy Tool for LangChain Agents

Custom web scraping framework
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

logger = setup_logger(__name__, log_file_path="logs/scrapy_tool.log")


class ScrapySecurityAgentState(AgentState):
    """Extended agent state for Scrapy operations."""
    user_id: str = ""


def _check_scrapy_installed() -> bool:
    """Check if Scrapy binary/package is installed."""
    return shutil.which("scrapy") is not None or True  # Adjust based on tool type


@tool
def scrapy_search(
    runtime: ToolRuntime,
    url: str,
    spider_name: str = "generic",
    follow_links: bool = False,
    max_pages: int = 10
) -> str:
    """
    Custom web scraping framework
    
    Args:
        runtime: ToolRuntime instance (automatically injected).
                url: str - Parameter description
        spider_name: str - Parameter description
        follow_links: bool - Parameter description
        max_pages: int - Parameter description
    
    Returns:
        JSON string with results.
    """
    try:
        safe_log_info(logger, f"[scrapy_search] Starting", url=url, spider_name=spider_name, follow_links=follow_links, max_pages=max_pages)
        
        # Validate inputs
        if not url or not isinstance(url, str) or not url.startswith(("http://", "https://")):
            error_msg = "Invalid URL provided (must start with http:// or https://)"
            safe_log_error(logger, error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        if max_pages < 1 or max_pages > 1000:
            error_msg = "Max pages must be between 1 and 1000"
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
        
        safe_log_info(logger, f"[scrapy_search] Complete", url=url)
        return json.dumps({"status": "error", "message": "Tool execution not yet implemented"})
        
    except Exception as e:
        safe_log_error(logger, f"[scrapy_search] Error: {str(e)}", exc_info=True)
        return json.dumps({"status": "error", "message": f"Scrapy scraping failed: {str(e)}"})
