"""
DNS Brute-forcer Tool for LangChain Agents

Attempts to identify hostnames through brute-forcing common names and iterations.
"""

import json
import os
from typing import Optional, Dict, Any, List
from langchain.tools import tool, ToolRuntime
from langchain.agents import AgentState
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error

logger = setup_logger(__name__, log_file_path="logs/spiderfoot_dnsbrute_tool.log")


class SfpDnsbruteSecurityAgentState(AgentState):
    """Extended agent state for DNS Brute-forcer operations."""
    user_id: str = ""


@tool
def sfp_dnsbrute(
    runtime: ToolRuntime,
    target: str,
    skipcommonwildcard: Optional[bool] = True,
    domainonly: Optional[bool] = True,
    commons: Optional[bool] = True,
    top10000: Optional[bool] = False,
    numbersuffix: Optional[bool] = True,
    numbersuffixlimit: Optional[bool] = True,
    **kwargs: Any
) -> str:
    """
    Attempts to identify hostnames through brute-forcing common names and iterations.
    
    Use Cases: Footprint, Investigate
    
    Args:
        runtime: ToolRuntime instance (automatically injected).
        target: Target to investigate (DOMAIN_NAME)
        skipcommonwildcard: If wildcard DNS is detected, don't bother brute-forcing.
        domainonly: Only attempt to brute-force names on domain names, not hostnames (some hostnames are also sub-domains).
        commons: Try a list of about 750 common hostnames/sub-domains.
        top10000: Try a further 10,000 common hostnames/sub-domains. Will make the scan much slower.
        numbersuffix: For any host found, try appending 1, 01, 001, -1, -01, -001, 2, 02, etc. (up to 10)
        numbersuffixlimit: Limit using the number suffixes for hosts that have already been resolved? If disabled this will significantly extend the duration of scans.
    
    Returns:
        JSON string with results.
    """
    try:
        safe_log_info(logger, f"[sfp_dnsbrute] Starting", target=target)
        
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
        # Import implementation function based on module type
        from hackerdogs_tools.osint.spiderfoot_modules._implementations import (
            implement_dnsbrute
        )
        
        # Execute migrated implementation
        implementation_result = implement_dnsbrute(
            target=target,
            skipcommonwildcard=skipcommonwildcard,
            domainonly=domainonly,
            commons=commons,
            top10000=top10000,
            numbersuffix=numbersuffix,
            numbersuffixlimit=numbersuffixlimit
        )
        
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
            "module": "sfp_dnsbrute",
            "module_name": "DNS Brute-forcer",
            "target": target,
            "raw_response": result_data,
            "user_id": user_id,
            "note": "Raw output from DNS Brute-forcer tool - migrated standalone implementation"
        }
        
        safe_log_info(logger, f"[sfp_dnsbrute] Complete", target=target, user_id=user_id)
        return json.dumps(result, indent=2)
        
    except Exception as e:
        # Safely get variables for error handling
        error_target = target if 'target' in locals() else kwargs.get("target", "unknown")
        error_user_id = runtime.state.get("user_id", "unknown") if 'runtime' in locals() else "unknown"
        safe_log_error(logger, f"[sfp_dnsbrute] Error: {str(e)}", target=error_target, user_id=error_user_id, exc_info=True)
        return json.dumps({
            "status": "error",
            "message": f"DNS Brute-forcer search failed: {str(e)}",
            "user_id": error_user_id
        })
