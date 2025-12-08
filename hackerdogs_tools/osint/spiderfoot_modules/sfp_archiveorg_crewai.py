"""
Archive.org Tool for CrewAI Agents

Identifies historic versions of interesting files/pages from the Wayback Machine.
Data Source: https://archive.org/
"""

import json
import os
from typing import Any, Optional, Dict, List
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error

logger = setup_logger(__name__, log_file_path="logs/spiderfoot_archiveorg_tool.log")




class SfpArchiveorgToolSchema(BaseModel):
    """Input schema for Archive.orgTool."""
    target: str = Field(..., description="Target to investigate (INTERESTING_FILE, URL_PASSWORD, URL_FORM, URL_FLASH, URL_STATIC, URL_JAVA_APPLET, URL_UPLOAD, URL_JAVASCRIPT, URL_WEB_FRAMEWORK)")
    farback: Optional[str] = Field(
        default="30,60,90",
        description="Number of days back to look for older versions of files/pages in the Wayback Machine snapshots. Comma-separate the values, so for example 30,60,90 means to look for snapshots 30 days, 60 days and 90 days back."
    )
    intfiles: Optional[bool] = Field(
        default=True,
        description="Query the Wayback Machine for historic versions of Interesting Files."
    )
    passwordpages: Optional[bool] = Field(
        default=True,
        description="Query the Wayback Machine for historic versions of URLs with passwords."
    )
    formpages: Optional[bool] = Field(
        default=False,
        description="Query the Wayback Machine for historic versions of URLs with forms."
    )
    flashpages: Optional[bool] = Field(
        default=False,
        description="Query the Wayback Machine for historic versions of URLs containing Flash."
    )
    javapages: Optional[bool] = Field(
        default=False,
        description="Query the Wayback Machine for historic versions of URLs using Java Applets."
    )
    staticpages: Optional[bool] = Field(
        default=False,
        description="Query the Wayback Machine for historic versions of purely static URLs."
    )
    uploadpages: Optional[bool] = Field(
        default=False,
        description="Query the Wayback Machine for historic versions of URLs accepting uploads."
    )
    webframeworkpages: Optional[bool] = Field(
        default=False,
        description="Query the Wayback Machine for historic versions of URLs using Javascript frameworks."
    )
    javascriptpages: Optional[bool] = Field(
        default=False,
        description="Query the Wayback Machine for historic versions of URLs using Javascript."
    )


class SfpArchiveorgTool(BaseTool):
    """Tool for Identifies historic versions of interesting files/pages from the Wayback Machine.."""
    
    name: str = "Archive.org"
    description: str = (
        "Identifies historic versions of interesting files/pages from the Wayback Machine."
        "\n\nUse Cases: Footprint, Passive"
        "\nCategories: Search Engines"
    )
    args_schema: type[BaseModel] = SfpArchiveorgToolSchema
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
    
    def _run(
        self,
        target: str,
        farback: Optional[str] = "30,60,90",
        intfiles: Optional[bool] = True,
        passwordpages: Optional[bool] = True,
        formpages: Optional[bool] = False,
        flashpages: Optional[bool] = False,
        javapages: Optional[bool] = False,
        staticpages: Optional[bool] = False,
        uploadpages: Optional[bool] = False,
        webframeworkpages: Optional[bool] = False,
        javascriptpages: Optional[bool] = False,
        **kwargs: Any
    ) -> str:
        """Execute Archive.org."""
        try:
            safe_log_info(logger, f"[SfpArchiveorgTool] Starting", target=target)
            
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
                implement_archiveorg
            )
            
            # Build parameters for the implementation function
            implementation_params = {
                "target": target,
                "farback": farback,
                "intfiles": intfiles,
                "passwordpages": passwordpages,
                "formpages": formpages,
                "flashpages": flashpages,
                "javapages": javapages,
                "staticpages": staticpages,
                "uploadpages": uploadpages,
                "webframeworkpages": webframeworkpages,
                "javascriptpages": javascriptpages,
            }
            
            # Execute migrated implementation
            implementation_result = implement_archiveorg(**implementation_params)
            
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
                "module": "sfp_archiveorg",
                "module_name": "Archive.org",
                "target": target,
                "raw_response": result_data,
                "user_id": user_id,
                "note": "Raw output from Archive.org tool - migrated standalone implementation"
            }
            
            safe_log_info(logger, f"[SfpArchiveorgTool] Complete", target=target, user_id=user_id)
            return json.dumps(result, indent=2)
            
        except Exception as e:
            target = kwargs.get("target", "unknown")
            user_id = kwargs.get("user_id", "")
            safe_log_error(logger, f"[SfpArchiveorgTool] Error: {str(e)}", target=target, user_id=user_id, exc_info=True)
            return json.dumps({
                "status": "error",
                "message": f"Archive.org search failed: {str(e)}",
                "user_id": user_id
            })
