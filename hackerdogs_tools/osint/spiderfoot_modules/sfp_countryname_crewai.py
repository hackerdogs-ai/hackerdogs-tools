"""
Country Name Extractor Tool for CrewAI Agents

Identify country names in any obtained data.
"""

import json
import os
from typing import Any, Optional, Dict, List
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error

logger = setup_logger(__name__, log_file_path="logs/spiderfoot_countryname_tool.log")




class SfpCountrynameToolSchema(BaseModel):
    """Input schema for Country Name ExtractorTool."""
    target: str = Field(..., description="Target to investigate (IBAN_NUMBER, PHONE_NUMBER, AFFILIATE_DOMAIN_NAME, CO_HOSTED_SITE_DOMAIN, DOMAIN_NAME, SIMILARDOMAIN, AFFILIATE_DOMAIN_WHOIS, CO_HOSTED_SITE_DOMAIN_WHOIS, DOMAIN_WHOIS, GEOINFO, PHYSICAL_ADDRESS)")
    cohosted: Optional[bool] = Field(
        default=True,
        description="Obtain country name from co-hosted sites"
    )
    affiliate: Optional[bool] = Field(
        default=True,
        description="Obtain country name from affiliate sites"
    )
    noncountrytld: Optional[bool] = Field(
        default=True,
        description="Parse TLDs not associated with any country as default country domains"
    )
    similardomain: Optional[bool] = Field(
        default=False,
        description="Obtain country name from similar domains"
    )


class SfpCountrynameTool(BaseTool):
    """Tool for Identify country names in any obtained data.."""
    
    name: str = "Country Name Extractor"
    description: str = (
        "Identify country names in any obtained data."
        "\n\nUse Cases: Footprint, Investigate, Passive"
        "\nCategories: Content Analysis"
    )
    args_schema: type[BaseModel] = SfpCountrynameToolSchema
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
    
    def _run(
        self,
        target: str,
        cohosted: Optional[bool] = True,
        affiliate: Optional[bool] = True,
        noncountrytld: Optional[bool] = True,
        similardomain: Optional[bool] = False,
        **kwargs: Any
    ) -> str:
        """Execute Country Name Extractor."""
        try:
            safe_log_info(logger, f"[SfpCountrynameTool] Starting", target=target)
            
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
            
            safe_log_info(logger, f"[SfpCountrynameTool] Complete", target=target, user_id=user_id)
            return json.dumps(result, indent=2)
            
        except Exception as e:
            target = kwargs.get("target", "unknown")
            user_id = kwargs.get("user_id", "")
            safe_log_error(logger, f"[SfpCountrynameTool] Error: {str(e)}", target=target, user_id=user_id, exc_info=True)
            return json.dumps({
                "status": "error",
                "message": f"Country Name Extractor search failed: {str(e)}",
                "user_id": user_id
            })
