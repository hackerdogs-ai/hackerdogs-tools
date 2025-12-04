"""
Scrapy Tool for CrewAI Agents

Custom web scraping framework
"""

import json
import subprocess
import shutil
from typing import Any, Optional, List
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error

logger = setup_logger(__name__, log_file_path="logs/scrapy_tool.log")


class ScrapyToolSchema(BaseModel):
    """Input schema for ScrapyTool."""
    url: str = Field(..., description="URL to scrape")
    spider_name: str = Field(default="generic", description="Spider name")
    follow_links: bool = Field(default=False, description="Follow links")
    max_pages: int = Field(default=10, ge=1, le=1000, description="Max pages to scrape (1-1000)")


class ScrapyTool(BaseTool):
    """Tool for Custom web scraping framework."""
    
    name: str = "Scrapy"
    description: str = "Custom web scraping framework"
    args_schema: type[BaseModel] = ScrapyToolSchema
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        # Add validation if needed
        # if not shutil.which("scrapy"):
        #     raise ValueError("Scrapy not found. Please install it.")
    
    def _run(
        self,
        url: str,
        spider_name: str = "generic",
        follow_links: bool = False,
        max_pages: int = 10,
        **kwargs: Any
    ) -> str:
        """Execute Scrapy web scraping."""
        try:
            safe_log_info(logger, f"[ScrapyTool] Starting", url=url, spider_name=spider_name, follow_links=follow_links, max_pages=max_pages)
            
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
            
            result_data = {
                "status": "success",
                "message": "Tool execution not yet implemented",
                "url": url,
                "spider_name": spider_name,
                "follow_links": follow_links,
                "max_pages": max_pages
            }
            
            safe_log_info(logger, f"[ScrapyTool] Complete", url=url)
            return json.dumps(result_data, indent=2)
            
        except Exception as e:
            safe_log_error(logger, f"[ScrapyTool] Error: {str(e)}", exc_info=True)
            return json.dumps({"status": "error", "message": f"Scrapy scraping failed: {str(e)}"})
