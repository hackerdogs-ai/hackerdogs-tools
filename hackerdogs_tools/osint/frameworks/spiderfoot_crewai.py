"""
SpiderFoot Tool for CrewAI Agents

Comprehensive OSINT framework
"""

import json
import subprocess
import shutil
from typing import Any, Optional, List
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error

logger = setup_logger(__name__, log_file_path="logs/spiderfoot_tool.log")


class SpiderFootToolSchema(BaseModel):
    """Input schema for SpiderFootTool."""
    target: str = Field(..., description="Target to investigate (IP, domain, URL, email, phone)")
    target_type: str = Field(..., description="Type of target: ip, domain, url, email, phone")
    modules: Optional[List[str]] = Field(default=None, description="Specific modules to run")
    scan_type: str = Field(default="footprint", description="Scan type: footprint, full, etc.")


class SpiderFootTool(BaseTool):
    """Tool for Comprehensive OSINT framework."""
    
    name: str = "SpiderFoot"
    description: str = "Comprehensive OSINT framework"
    args_schema: type[BaseModel] = SpiderFootToolSchema
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        # Add validation if needed
        # if not shutil.which("spiderfoot"):
        #     raise ValueError("SpiderFoot not found. Please install it.")
    
    def _run(
        self,
        target: str,
        target_type: str,
        modules: Optional[List[str]] = None,
        scan_type: str = "footprint",
        **kwargs: Any
    ) -> str:
        """Execute SpiderFoot OSINT investigation."""
        try:
            safe_log_info(logger, f"[SpiderFootTool] Starting", target=target, target_type=target_type, modules=modules, scan_type=scan_type)
            
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
                "scan_type": scan_type
            }
            
            safe_log_info(logger, f"[SpiderFootTool] Complete", target=target)
            return json.dumps(result_data, indent=2)
            
        except Exception as e:
            safe_log_error(logger, f"[SpiderFootTool] Error: {str(e)}", exc_info=True)
            return json.dumps({"status": "error", "message": f"SpiderFoot search failed: {str(e)}"})
