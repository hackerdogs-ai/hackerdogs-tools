"""
Port Scanner - TCP Tool for CrewAI Agents

Scans for commonly open TCP ports on Internet-facing systems.
"""

import json
import os
from typing import Any, Optional, Dict, List
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error

logger = setup_logger(__name__, log_file_path="logs/spiderfoot_portscan_tcp_tool.log")


class SfpPortscantcpToolSchema(BaseModel):
    """Input schema for Port Scanner - TCPTool."""
    target: str = Field(..., description="Target to investigate (IP_ADDRESS, NETBLOCK_OWNER)")
    ports: Optional[List[Any]] = Field(
        default=['21', '22', '23', '25', '53', '79', '80', '81', '88', '110', '111', '113', '119', '123', '137', '138', '139', '143', '161', '179', '389', '443', '445', '465', '512', '513', '514', '515', '3306', '5432', '1521', '2638', '1433', '3389', '5900', '5901', '5902', '5903', '5631', '631', '636', '990', '992', '993', '995', '1080', '8080', '8888', '9000'],
        description="The TCP ports to scan. Prefix with an '@' to iterate through a file containing ports to try (one per line), e.g. @C:\\ports.txt or @/home/bob/ports.txt. Or supply a URL to load the list from there."
    )
    timeout: Optional[int] = Field(
        default=15,
        description="Seconds before giving up on a port."
    )
    maxthreads: Optional[int] = Field(
        default=10,
        description="Number of ports to try to open simultaneously (number of threads to spawn at once.)"
    )
    randomize: Optional[bool] = Field(
        default=True,
        description="Randomize the order of ports scanned."
    )
    netblockscan: Optional[bool] = Field(
        default=True,
        description="Port scan all IPs within identified owned netblocks?"
    )
    netblockscanmax: Optional[int] = Field(
        default=24,
        description="Maximum netblock/subnet size to scan IPs within (CIDR value, 24 = /24, 16 = /16, etc.)"
    )


class SfpPortscantcpTool(BaseTool):
    """Tool for Scans for commonly open TCP ports on Internet-facing systems.."""
    
    name: str = "Port Scanner - TCP"
    description: str = (
        "Scans for commonly open TCP ports on Internet-facing systems."
        "\n\nUse Cases: Footprint, Investigate"
        "\nCategories: Crawling and Scanning"
    )
    args_schema: type[BaseModel] = SfpPortscantcpToolSchema
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
    
    def _run(
        self,
        target: str,
        ports: Optional[List[Any]] = ['21', '22', '23', '25', '53', '79', '80', '81', '88', '110', '111', '113', '119', '123', '137', '138', '139', '143', '161', '179', '389', '443', '445', '465', '512', '513', '514', '515', '3306', '5432', '1521', '2638', '1433', '3389', '5900', '5901', '5902', '5903', '5631', '631', '636', '990', '992', '993', '995', '1080', '8080', '8888', '9000'],
        timeout: Optional[int] = 15,
        maxthreads: Optional[int] = 10,
        randomize: Optional[bool] = True,
        netblockscan: Optional[bool] = True,
        netblockscanmax: Optional[int] = 24,
        **kwargs: Any
    ) -> str:
        """Execute Port Scanner - TCP."""
        try:
            safe_log_info(logger, f"[SfpPortscantcpTool] Starting", target=target)
            
            # Get user_id from kwargs
            user_id = kwargs.get("user_id", "")
            
            # Validate inputs
            if not target or not isinstance(target, str) or len(target.strip()) == 0:
                error_msg = "Invalid target provided"
                safe_log_error(logger, error_msg, target=target, user_id=user_id)
                return json.dumps({
                    "status": "error",
                    "message": error_msg,
                    "user_id": user_id
                })
            
            
            # MIGRATED IMPLEMENTATION - Direct execution, no Docker, no SpiderFoot dependencies
            # Import implementation function dynamically
            from hackerdogs_tools.osint.spiderfoot_modules._implementations import (
                implement_portscan_tcp
            )
            
            # Build parameters for the implementation function
            implementation_params = {
                "target": target,
                "ports": ports,
                "timeout": timeout,
                "maxthreads": maxthreads,
                "randomize": randomize,
                "netblockscan": netblockscan,
                "netblockscanmax": netblockscanmax,
            }
            
            # Execute migrated implementation
            implementation_result = implement_portscan_tcp(**implementation_params)
            
            # Use implementation result
            if implementation_result.get("status") == "error":
                error_msg = implementation_result.get("message", "Unknown error")
                safe_log_error(logger, error_msg, target=target, user_id=user_id)
                return json.dumps({
                    "status": "error",
                    "message": error_msg,
                    "user_id": user_id
                })
            
            result_data = implementation_result
            
            # Return verbatim output with consistent structure
            result = {
                "status": "success",
                "module": "sfp_portscan_tcp",
                "module_name": "Port Scanner - TCP",
                "target": target,
                "raw_response": result_data,
                "user_id": user_id,
                "note": "Raw output from Port Scanner - TCP tool - migrated standalone implementation"
            }
            
            safe_log_info(logger, f"[SfpPortscantcpTool] Complete", target=target, user_id=user_id)
            return json.dumps(result, indent=2)
            
        except Exception as e:
            target = kwargs.get("target", "unknown")
            user_id = kwargs.get("user_id", "")
            safe_log_error(logger, f"[SfpPortscantcpTool] Error: {str(e)}", target=target, user_id=user_id, exc_info=True)
            return json.dumps({
                "status": "error",
                "message": f"Port Scanner - TCP search failed: {str(e)}",
                "user_id": user_id
            })
