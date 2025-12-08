"""
Account Finder Tool for CrewAI Agents

Look for possible associated accounts on over 500 social and other websites such as Instagram, Reddit, etc.
"""

import json
import os
from typing import Any, Optional, Dict, List
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error

logger = setup_logger(__name__, log_file_path="logs/spiderfoot_accounts_tool.log")




class SfpAccountsToolSchema(BaseModel):
    """Input schema for Account FinderTool."""
    target: str = Field(..., description="Target to investigate (EMAILADDR, DOMAIN_NAME, HUMAN_NAME, USERNAME)")
    ignorenamedict: Optional[bool] = Field(
        default=True,
        description="Don't bother looking up names that are just stand-alone first names (too many false positives)."
    )
    ignoreworddict: Optional[bool] = Field(
        default=True,
        description="Don't bother looking up names that appear in the dictionary."
    )
    musthavename: Optional[bool] = Field(
        default=True,
        description="The username must be mentioned on the social media page to consider it valid (helps avoid false positives)."
    )
    userfromemail: Optional[bool] = Field(
        default=True,
        description="Extract usernames from e-mail addresses at all? If disabled this can reduce false positives for common usernames but for highly unique usernames it would result in missed accounts."
    )
    permutate: Optional[bool] = Field(
        default=False,
        description="Look for the existence of account name permutations. Useful to identify fraudulent social media accounts or account squatting."
    )
    usernamesize: Optional[int] = Field(
        default=4,
        description="The minimum length of a username to query across social media sites. Helps avoid false positives for very common short usernames."
    )


class SfpAccountsTool(BaseTool):
    """Tool for Look for possible associated accounts on over 500 social and other websites such as Instagram, Reddit, etc.."""
    
    name: str = "Account Finder"
    description: str = (
        "Look for possible associated accounts on over 500 social and other websites such as Instagram, Reddit, etc."
        "\n\nUse Cases: Footprint, Passive"
        "\nCategories: Social Media"
    )
    args_schema: type[BaseModel] = SfpAccountsToolSchema
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
    
    def _run(
        self,
        target: str,
        ignorenamedict: Optional[bool] = True,
        ignoreworddict: Optional[bool] = True,
        musthavename: Optional[bool] = True,
        userfromemail: Optional[bool] = True,
        permutate: Optional[bool] = False,
        usernamesize: Optional[int] = 4,
        **kwargs: Any
    ) -> str:
        """Execute Account Finder."""
        try:
            safe_log_info(logger, f"[SfpAccountsTool] Starting", target=target)
            
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
                implement_accounts
            )
            
            # Build parameters for the implementation function
            implementation_params = {
                "target": target,
                "ignorenamedict": ignorenamedict,
                "ignoreworddict": ignoreworddict,
                "musthavename": musthavename,
                "userfromemail": userfromemail,
                "permutate": permutate,
                "usernamesize": usernamesize,
            }
            
            # Execute migrated implementation
            implementation_result = implement_accounts(**implementation_params)
            
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
                "module": "sfp_accounts",
                "module_name": "Account Finder",
                "target": target,
                "raw_response": result_data,
                "user_id": user_id,
                "note": "Raw output from Account Finder tool - migrated standalone implementation"
            }
            
            safe_log_info(logger, f"[SfpAccountsTool] Complete", target=target, user_id=user_id)
            return json.dumps(result, indent=2)
            
        except Exception as e:
            target = kwargs.get("target", "unknown")
            user_id = kwargs.get("user_id", "")
            safe_log_error(logger, f"[SfpAccountsTool] Error: {str(e)}", target=target, user_id=user_id, exc_info=True)
            return json.dumps({
                "status": "error",
                "message": f"Account Finder search failed: {str(e)}",
                "user_id": user_id
            })
