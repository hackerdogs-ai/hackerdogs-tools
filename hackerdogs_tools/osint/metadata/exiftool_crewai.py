"""
ExifTool Tool for CrewAI Agents

Extract metadata from images/PDFs
"""

import json
import subprocess
import shutil
from typing import Any, Optional, List
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error

logger = setup_logger(__name__, log_file_path="logs/exiftool_tool.log")


class ExifToolToolSchema(BaseModel):
    """Input schema for ExifToolTool."""
    file_path: str = Field(..., description="Path to image or PDF file")
    extract_gps: bool = Field(default=True, description="Extract GPS coordinates")
    extract_author: bool = Field(default=True, description="Extract author information")


class ExifToolTool(BaseTool):
    """Tool for Extract metadata from images/PDFs."""
    
    name: str = "ExifTool"
    description: str = "Extract metadata from images/PDFs"
    args_schema: type[BaseModel] = ExifToolToolSchema
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        # Add validation if needed
        # if not shutil.which("exiftool"):
        #     raise ValueError("ExifTool not found. Please install it.")
    
    def _run(
        self,
        file_path: str,
        extract_gps: bool = True,
        extract_author: bool = True,
        **kwargs: Any
    ) -> str:
        """Execute ExifTool metadata extraction."""
        try:
            safe_log_info(logger, f"[ExifToolTool] Starting", file_path=file_path, extract_gps=extract_gps, extract_author=extract_author)
            
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
            
            result_data = {
                "status": "success",
                "message": "Tool execution not yet implemented",
                "file_path": file_path,
                "extract_gps": extract_gps,
                "extract_author": extract_author
            }
            
            safe_log_info(logger, f"[ExifToolTool] Complete", file_path=file_path)
            return json.dumps(result_data, indent=2)
            
        except Exception as e:
            safe_log_error(logger, f"[ExifToolTool] Error: {str(e)}", exc_info=True)
            return json.dumps({"status": "error", "message": f"ExifTool extraction failed: {str(e)}"})
