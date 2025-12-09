"""
Custom Threat Feed Tool for LangChain Agents

Check if a host/domain, netblock, ASN or IP is malicious according to your custom feed.
"""

import json
import os
from typing import Optional, Dict, Any, List
from langchain.tools import tool, ToolRuntime
from langchain.agents import AgentState
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error

logger = setup_logger(__name__, log_file_path="logs/spiderfoot_customfeed_tool.log")


class SfpCustomfeedSecurityAgentState(AgentState):
    """Extended agent state for Custom Threat Feed operations."""
    user_id: str = ""




@tool
def sfp_customfeed(
    runtime: ToolRuntime,
    target: str,
    checkaffiliates: Optional[bool] = True,
    checkcohosts: Optional[bool] = True,
    url: Optional[str] = "",
    cacheperiod: Optional[int] = 0,
    **kwargs: Any
) -> str:
    """
    Check if a host/domain, netblock, ASN or IP is malicious according to your custom feed.
    
    Use Cases: Investigate, Passive
    
    Args:
        runtime: ToolRuntime instance (automatically injected).
        target: Target to investigate (INTERNET_NAME, IP_ADDRESS, AFFILIATE_INTERNET_NAME, AFFILIATE_IPADDR, CO_HOSTED_SITE)
        url: The URL where the feed can be found. Exact matching is performed so the format must be a single line per host, ASN, domain, IP or netblock.
        checkaffiliates: Apply checks to affiliates?
        checkcohosts: Apply checks to sites found to be co-hosted on the target's IP?
        cacheperiod: Maximum age of data in hours before re-downloading. 0 to always download.
    
    Returns:
        JSON string with results.
    """
    try:
        safe_log_info(logger, f"[sfp_customfeed] Starting", target=target)
        
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
            implement_customfeed
        )
        
        # Build parameters for the implementation function
        # Note: checkaffiliates and checkcohosts are event-level filters, not implementation parameters
        implementation_params = {
            "target": target,
            "url": url,
            "target_type": None,  # Auto-detected in implementation
            "cacheperiod": cacheperiod,
        }
        
        # Execute migrated implementation
        implementation_result = implement_customfeed(**implementation_params)
        
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
            "module": "sfp_customfeed",
            "module_name": "Custom Threat Feed",
            "target": target,
            "raw_response": result_data,
            "user_id": user_id,
            "note": "Raw output from Custom Threat Feed tool - migrated standalone implementation"
        }
        
        safe_log_info(logger, f"[sfp_customfeed] Complete", target=target, user_id=user_id)
        return json.dumps(result, indent=2)
        
    except Exception as e:
        # Safely get variables for error handling
        error_target = target if 'target' in locals() else kwargs.get("target", "unknown")
        error_user_id = runtime.state.get("user_id", "unknown") if 'runtime' in locals() else "unknown"
        safe_log_error(logger, f"[sfp_customfeed] Error: {str(e)}", target=error_target, user_id=error_user_id, exc_info=True)
        return json.dumps({
            "status": "error",
            "message": f"Custom Threat Feed search failed: {str(e)}",
            "user_id": error_user_id
        })
