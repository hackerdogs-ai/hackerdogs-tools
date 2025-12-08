"""
Country Name Extractor Tool for LangChain Agents

Identify country names in any obtained data.
"""

import json
import os
from typing import Optional, Dict, Any, List
from langchain.tools import tool, ToolRuntime
from langchain.agents import AgentState
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error

logger = setup_logger(__name__, log_file_path="logs/spiderfoot_countryname_tool.log")


class SfpCountrynameSecurityAgentState(AgentState):
    """Extended agent state for Country Name Extractor operations."""
    user_id: str = ""




@tool
def sfp_countryname(
    runtime: ToolRuntime,
    target: str,
    cohosted: Optional[bool] = True,
    affiliate: Optional[bool] = True,
    noncountrytld: Optional[bool] = True,
    similardomain: Optional[bool] = False,
    **kwargs: Any
) -> str:
    """
    Identify country names in any obtained data.
    
    Use Cases: Footprint, Investigate, Passive
    
    Args:
        runtime: ToolRuntime instance (automatically injected).
        target: Target to investigate (IBAN_NUMBER, PHONE_NUMBER, AFFILIATE_DOMAIN_NAME, CO_HOSTED_SITE_DOMAIN, DOMAIN_NAME, SIMILARDOMAIN, AFFILIATE_DOMAIN_WHOIS, CO_HOSTED_SITE_DOMAIN_WHOIS, DOMAIN_WHOIS, GEOINFO, PHYSICAL_ADDRESS)
        cohosted: Obtain country name from co-hosted sites
        affiliate: Obtain country name from affiliate sites
        noncountrytld: Parse TLDs not associated with any country as default country domains
        similardomain: Obtain country name from similar domains
    
    Returns:
        JSON string with results.
    """
    try:
        safe_log_info(logger, f"[sfp_countryname] Starting", target=target)
        
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
            implement_countryname
        )
        
        # Build parameters for the implementation function
        implementation_params = {
            "target": target,
            "cohosted": cohosted,
            "affiliate": affiliate,
            "noncountrytld": noncountrytld,
            "similardomain": similardomain,
        }
        
        # Execute migrated implementation
        implementation_result = implement_countryname(**implementation_params)
        
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
            "module": "sfp_countryname",
            "module_name": "Country Name Extractor",
            "target": target,
            "raw_response": result_data,
            "user_id": user_id,
            "note": "Raw output from Country Name Extractor tool - migrated standalone implementation"
        }
        
        safe_log_info(logger, f"[sfp_countryname] Complete", target=target, user_id=user_id)
        return json.dumps(result, indent=2)
        
    except Exception as e:
        # Safely get variables for error handling
        error_target = target if 'target' in locals() else kwargs.get("target", "unknown")
        error_user_id = runtime.state.get("user_id", "unknown") if 'runtime' in locals() else "unknown"
        safe_log_error(logger, f"[sfp_countryname] Error: {str(e)}", target=error_target, user_id=error_user_id, exc_info=True)
        return json.dumps({
            "status": "error",
            "message": f"Country Name Extractor search failed: {str(e)}",
            "user_id": error_user_id
        })
