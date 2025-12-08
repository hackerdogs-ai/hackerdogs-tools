"""
Port Scanner - TCP Tool for LangChain Agents

Scans for commonly open TCP ports on Internet-facing systems.
"""

import json
import os
from typing import Optional, Dict, Any, List
from langchain.tools import tool, ToolRuntime
from langchain.agents import AgentState
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error

logger = setup_logger(__name__, log_file_path="logs/spiderfoot_portscan_tcp_tool.log")


class SfpPortscantcpSecurityAgentState(AgentState):
    """Extended agent state for Port Scanner - TCP operations."""
    user_id: str = ""


@tool
def sfp_portscan_tcp(
    runtime: ToolRuntime,
    target: str,
    ports: Optional[List[Any]] = ['21', '22', '23', '25', '53', '79', '80', '81', '88', '110', '111', '113', '119', '123', '137', '138', '139', '143', '161', '179', '389', '443', '445', '465', '512', '513', '514', '515', '3306', '5432', '1521', '2638', '1433', '3389', '5900', '5901', '5902', '5903', '5631', '631', '636', '990', '992', '993', '995', '1080', '8080', '8888', '9000'],
    timeout: Optional[int] = 15,
    maxthreads: Optional[int] = 10,
    randomize: Optional[bool] = True,
    netblockscan: Optional[bool] = True,
    netblockscanmax: Optional[int] = 24,
    **kwargs: Any
) -> str:
    """
    Scans for commonly open TCP ports on Internet-facing systems.
    
    Use Cases: Footprint, Investigate
    
    Args:
        runtime: ToolRuntime instance (automatically injected).
        target: Target to investigate (IP_ADDRESS, NETBLOCK_OWNER)
        maxthreads: Number of ports to try to open simultaneously (number of threads to spawn at once.)
        ports: The TCP ports to scan. Prefix with an '@' to iterate through a file containing ports to try (one per line), e.g. @C:\\ports.txt or @/home/bob/ports.txt. Or supply a URL to load the list from there.
        timeout: Seconds before giving up on a port.
        randomize: Randomize the order of ports scanned.
        netblockscan: Port scan all IPs within identified owned netblocks?
        netblockscanmax: Maximum netblock/subnet size to scan IPs within (CIDR value, 24 = /24, 16 = /16, etc.)
    
    Returns:
        JSON string with results.
    """
    try:
        safe_log_info(logger, f"[sfp_portscan_tcp] Starting", target=target)
        
        # Get user_id from runtime state
        user_id = runtime.state.get("user_id", "unknown")
        
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
        
        safe_log_info(logger, f"[sfp_portscan_tcp] Complete", target=target, user_id=user_id)
        return json.dumps(result, indent=2)
        
    except Exception as e:
        # Safely get variables for error handling
        error_target = target if 'target' in locals() else kwargs.get("target", "unknown")
        error_user_id = runtime.state.get("user_id", "unknown") if 'runtime' in locals() else "unknown"
        safe_log_error(logger, f"[sfp_portscan_tcp] Error: {str(e)}", target=error_target, user_id=error_user_id, exc_info=True)
        return json.dumps({
            "status": "error",
            "message": f"Port Scanner - TCP search failed: {str(e)}",
            "user_id": error_user_id
        })
