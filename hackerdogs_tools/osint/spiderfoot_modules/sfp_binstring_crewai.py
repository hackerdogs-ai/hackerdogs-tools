"""
Binary String Extractor Tool for CrewAI Agents

Attempt to identify strings in binary content.
"""

import json
import os
from typing import Any, Optional, Dict, List
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error

logger = setup_logger(__name__, log_file_path="logs/spiderfoot_binstring_tool.log")




class SfpBinstringToolSchema(BaseModel):
    """Input schema for Binary String ExtractorTool."""
    target: str = Field(..., description="Target to investigate (LINKED_URL_INTERNAL)")
    minwordsize: Optional[int] = Field(
        default=5,
        description="Upon finding a string in a binary, ensure it is at least this length. Helps weed out false positives."
    )
    maxwords: Optional[int] = Field(
        default=100,
        description="Stop reporting strings from a single binary after this many are found."
    )
    maxfilesize: Optional[int] = Field(
        default=1000000,
        description="Maximum file size in bytes to download for analysis."
    )
    usedict: Optional[bool] = Field(
        default=True,
        description="Use the dictionary to further reduce false positives - any string found must contain a word from the dictionary (can be very slow, especially for larger files)."
    )
    fileexts: Optional[List[Any]] = Field(
        default=['png', 'gif', 'jpg', 'jpeg', 'tiff', 'tif', 'ico', 'flv', 'mp4', 'mp3', 'avi', 'mpg', 'mpeg', 'dat', 'mov', 'swf', 'exe', 'bin'],
        description="File types to fetch and analyse."
    )
    filterchars: Optional[str] = Field(
        default="#}{|%^&*()=+,;[]~",
        description="Ignore strings with these characters, as they may just be garbage ASCII."
    )


class SfpBinstringTool(BaseTool):
    """Tool for Attempt to identify strings in binary content.."""
    
    name: str = "Binary String Extractor"
    description: str = (
        "Attempt to identify strings in binary content."
        "\n\nUse Cases: Footprint"
        "\nCategories: Content Analysis"
    )
    args_schema: type[BaseModel] = SfpBinstringToolSchema
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
    
    def _run(
        self,
        target: str,
        minwordsize: Optional[int] = 5,
        maxwords: Optional[int] = 100,
        maxfilesize: Optional[int] = 1000000,
        usedict: Optional[bool] = True,
        fileexts: Optional[List[Any]] = ['png', 'gif', 'jpg', 'jpeg', 'tiff', 'tif', 'ico', 'flv', 'mp4', 'mp3', 'avi', 'mpg', 'mpeg', 'dat', 'mov', 'swf', 'exe', 'bin'],
        filterchars: Optional[str] = "#}{|%^&*()=+,;[]~",
        **kwargs: Any
    ) -> str:
        """Execute Binary String Extractor."""
        try:
            safe_log_info(logger, f"[SfpBinstringTool] Starting", target=target)
            
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
                implement_binstring
            )
            
            # Build parameters for the implementation function
            implementation_params = {
                "target": target,
                "minwordsize": minwordsize,
                "maxwords": maxwords,
                "maxfilesize": maxfilesize,
                "usedict": usedict,
                "fileexts": fileexts,
                "filterchars": filterchars,
            }
            
            # Execute migrated implementation
            implementation_result = implement_binstring(**implementation_params)
            
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
                "module": "sfp_binstring",
                "module_name": "Binary String Extractor",
                "target": target,
                "raw_response": result_data,
                "user_id": user_id,
                "note": "Raw output from Binary String Extractor tool - migrated standalone implementation"
            }
            
            safe_log_info(logger, f"[SfpBinstringTool] Complete", target=target, user_id=user_id)
            return json.dumps(result, indent=2)
            
        except Exception as e:
            target = kwargs.get("target", "unknown")
            user_id = kwargs.get("user_id", "")
            safe_log_error(logger, f"[SfpBinstringTool] Error: {str(e)}", target=target, user_id=user_id, exc_info=True)
            return json.dumps({
                "status": "error",
                "message": f"Binary String Extractor search failed: {str(e)}",
                "user_id": user_id
            })
