"""
Company Name Extractor Tool for LangChain Agents

Identify company names in any obtained data.
"""

import json
import os
from typing import Optional, Dict, Any, List
from langchain.tools import tool, ToolRuntime
from langchain.agents import AgentState
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error

logger = setup_logger(__name__, log_file_path="logs/spiderfoot_company_tool.log")


class SfpCompanySecurityAgentState(AgentState):
    """Extended agent state for Company Name Extractor operations."""
    user_id: str = ""




@tool
def sfp_company(
    runtime: ToolRuntime,
    target: str,
    filterjscss: Optional[bool] = True,
    **kwargs: Any
) -> str:
    """
    Identify company names in any obtained data.
    
    Use Cases: Footprint, Investigate, Passive
    
    Args:
        runtime: ToolRuntime instance (automatically injected).
        target: Target to investigate (TARGET_WEB_CONTENT, SSL_CERTIFICATE_ISSUED, DOMAIN_WHOIS, NETBLOCK_WHOIS, AFFILIATE_DOMAIN_WHOIS, AFFILIATE_WEB_CONTENT)
        filterjscss: Filter out company names that originated from CSS/JS content. Enabling this avoids detection of popular Javascript and web framework author company names.
    
    Returns:
        JSON string with results.
    """
    try:
        safe_log_info(logger, f"[sfp_company] Starting", target=target)
        
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
            implement_company
        )
        
        # Build parameters for the implementation function
        implementation_params = {
            "target": target,
            "filterjscss": filterjscss,
        }
        
        # Execute migrated implementation
        implementation_result = implement_company(**implementation_params)
        
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
            "module": "sfp_company",
            "module_name": "Company Name Extractor",
            "target": target,
            "raw_response": result_data,
            "user_id": user_id,
            "note": "Raw output from Company Name Extractor tool - migrated standalone implementation"
        }
        
        safe_log_info(logger, f"[sfp_company] Complete", target=target, user_id=user_id)
        return json.dumps(result, indent=2)
        
    except Exception as e:
        # Safely get variables for error handling
        error_target = target if 'target' in locals() else kwargs.get("target", "unknown")
        error_user_id = runtime.state.get("user_id", "unknown") if 'runtime' in locals() else "unknown"
        safe_log_error(logger, f"[sfp_company] Error: {str(e)}", target=error_target, user_id=error_user_id, exc_info=True)
        return json.dumps({
            "status": "error",
            "message": f"Company Name Extractor search failed: {str(e)}",
            "user_id": error_user_id
        })
