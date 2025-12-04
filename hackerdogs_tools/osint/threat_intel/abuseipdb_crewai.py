"""
AbuseIPDB Tool for CrewAI Agents

IP reputation and abuse checking
"""

import json
import subprocess
import shutil
from typing import Any, Optional, List
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error

logger = setup_logger(__name__, log_file_path="logs/abuseipdb_tool.log")


class AbuseIPDBToolSchema(BaseModel):
    """Input schema for AbuseIPDBTool."""
    ip: str = Field(..., description="IP address to check")
    max_age_in_days: int = Field(default=90, ge=1, le=365, description="Max age in days (1-365)")
    verbose: bool = Field(default=True, description="Verbose output")


class AbuseIPDBTool(BaseTool):
    """Tool for IP reputation and abuse checking."""
    
    name: str = "AbuseIPDB"
    description: str = "IP reputation and abuse checking"
    args_schema: type[BaseModel] = AbuseIPDBToolSchema
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        # Add validation if needed
        # if not shutil.which("abuseipdb"):
        #     raise ValueError("AbuseIPDB not found. Please install it.")
    
    def _run(
        self,
        ip: str,
        max_age_in_days: int = 90,
        verbose: bool = True,
        **kwargs: Any
    ) -> str:
        """Execute AbuseIPDB IP check."""
        try:
            safe_log_info(logger, f"[AbuseIPDBTool] Starting", ip=ip, max_age_in_days=max_age_in_days, verbose=verbose)
            
            # Validate inputs
            if not ip or not isinstance(ip, str):
                error_msg = "Invalid IP address provided"
                safe_log_error(logger, error_msg)
                return json.dumps({"status": "error", "message": error_msg})
            
            if max_age_in_days < 1 or max_age_in_days > 365:
                error_msg = "Max age must be between 1 and 365 days"
                safe_log_error(logger, error_msg)
                return json.dumps({"status": "error", "message": error_msg})
            
            # Note: AbuseIPDB is an API service, not a binary tool
            # This would use API calls, not Docker
            
            # TODO: Implement tool-specific logic
            # This is a template - implement actual tool execution
            
            result_data = {
                "status": "success",
                "message": "Tool execution not yet implemented",
                "ip": ip,
                "max_age_in_days": max_age_in_days,
                "verbose": verbose
            }
            
            safe_log_info(logger, f"[AbuseIPDBTool] Complete", ip=ip)
            return json.dumps(result_data, indent=2)
            
        except Exception as e:
            safe_log_error(logger, f"[AbuseIPDBTool] Error: {str(e)}", exc_info=True)
            return json.dumps({"status": "error", "message": f"AbuseIPDB check failed: {str(e)}"})
