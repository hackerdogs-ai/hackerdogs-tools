"""
ZMap Tool for CrewAI Agents

Single-packet scanning
"""

import json
import subprocess
import shutil
from typing import Any, Optional, List
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error

logger = setup_logger(__name__, log_file_path="logs/zmap_tool.log")


class ZMapToolSchema(BaseModel):
    """Input schema for ZMapTool."""
    ip_range: str = Field(..., description="IP range or CIDR to scan")
    port: int = Field(..., description="Port to scan (1-65535)", ge=1, le=65535)
    bandwidth: str = Field(..., description="Bandwidth limit (e.g., '10M', '1G')")


class ZMapTool(BaseTool):
    """Tool for Single-packet scanning."""
    
    name: str = "ZMap"
    description: str = "Single-packet scanning"
    args_schema: type[BaseModel] = ZMapToolSchema
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        # Add validation if needed
        # if not shutil.which("zmap"):
        #     raise ValueError("ZMap not found. Please install it.")
    
    def _run(
        self,
        ip_range: str,
        port: int,
        bandwidth: str,
        **kwargs: Any
    ) -> str:
        """Execute ZMap single-packet scan."""
        try:
            safe_log_info(logger, f"[ZMapTool] Starting", ip_range=ip_range, port=port, bandwidth=bandwidth)
            
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
                "bandwidth": bandwidth
            }
            
            safe_log_info(logger, f"[ZMapTool] Complete", ip_range=ip_range, port=port)
            return json.dumps(result_data, indent=2)
            
        except Exception as e:
            safe_log_error(logger, f"[ZMapTool] Error: {str(e)}", exc_info=True)
            return json.dumps({"status": "error", "message": f"ZMap scan failed: {str(e)}"})
