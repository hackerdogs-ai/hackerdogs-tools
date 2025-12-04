"""
Masscan Tool for CrewAI Agents

Fast Internet port scanner
"""

import json
import subprocess
import shutil
from typing import Any, Optional, List
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error

logger = setup_logger(__name__, log_file_path="logs/masscan_tool.log")


class MasscanToolSchema(BaseModel):
    """Input schema for MasscanTool."""
    ip_range: str = Field(..., description="IP range or CIDR to scan (e.g., '10.0.0.0/8')")
    ports: str = Field(..., description="Ports to scan (e.g., '80,443,8080' or '1-1000')")
    rate: int = Field(default=1000, ge=1, le=10000000, description="Scan rate (packets per second, 1-10000000)")


class MasscanTool(BaseTool):
    """Tool for Fast Internet port scanner."""
    
    name: str = "Masscan"
    description: str = "Fast Internet port scanner"
    args_schema: type[BaseModel] = MasscanToolSchema
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        # Add validation if needed
        # if not shutil.which("masscan"):
        #     raise ValueError("Masscan not found. Please install it.")
    
    def _run(
        self,
        ip_range: str,
        ports: str,
        rate: int = 1000,
        **kwargs: Any
    ) -> str:
        """Execute Masscan port scan."""
        try:
            safe_log_info(logger, f"[MasscanTool] Starting", ip_range=ip_range, ports=ports, rate=rate)
            
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
                "rate": rate
            }
            
            safe_log_info(logger, f"[MasscanTool] Complete", ip_range=ip_range)
            return json.dumps(result_data, indent=2)
            
        except Exception as e:
            safe_log_error(logger, f"[MasscanTool] Error: {str(e)}", exc_info=True)
            return json.dumps({"status": "error", "message": f"Masscan scan failed: {str(e)}"})
