"""
File Metadata Extractor Tool for CrewAI Agents

Extracts meta data from documents and images.
"""

import json
import os
from typing import Any, Optional, Dict, List
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error

logger = setup_logger(__name__, log_file_path="logs/spiderfoot_filemeta_tool.log")




class SfpFilemetaToolSchema(BaseModel):
    """Input schema for File Metadata ExtractorTool."""
    target: str = Field(..., description="Target to investigate (LINKED_URL_INTERNAL, INTERESTING_FILE)")
    fileexts: Optional[List[Any]] = Field(
        default=['docx', 'pptx', 'pdf', 'jpg', 'jpeg', 'tiff', 'tif'],
        description="File extensions of files you want to analyze the meta data of (only PDF, DOCX, XLSX and PPTX are supported.)"
    )
    timeout: Optional[int] = Field(
        default=300,
        description="Download timeout for files, in seconds."
    )


class SfpFilemetaTool(BaseTool):
    """Tool for Extracts meta data from documents and images.."""
    
    name: str = "File Metadata Extractor"
    description: str = (
        "Extracts meta data from documents and images."
        "\n\nUse Cases: Footprint"
        "\nCategories: Content Analysis"
    )
    args_schema: type[BaseModel] = SfpFilemetaToolSchema
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
    
    def _run(
        self,
        target: str,
        fileexts: Optional[List[Any]] = ['docx', 'pptx', 'pdf', 'jpg', 'jpeg', 'tiff', 'tif'],
        timeout: Optional[int] = 300,
        **kwargs: Any
    ) -> str:
        """Execute File Metadata Extractor."""
        try:
            safe_log_info(logger, f"[SfpFilemetaTool] Starting", target=target)
            
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
                implement_filemeta
            )
            
            # Build parameters for the implementation function
            implementation_params = {
                "target": target,
                "fileexts": fileexts,
                "timeout": timeout,
            }
            
            # Execute migrated implementation
            implementation_result = implement_filemeta(**implementation_params)
            
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
                "module": "sfp_filemeta",
                "module_name": "File Metadata Extractor",
                "target": target,
                "raw_response": result_data,
                "user_id": user_id,
                "note": "Raw output from File Metadata Extractor tool - migrated standalone implementation"
            }
            
            safe_log_info(logger, f"[SfpFilemetaTool] Complete", target=target, user_id=user_id)
            return json.dumps(result, indent=2)
            
        except Exception as e:
            target = kwargs.get("target", "unknown")
            user_id = kwargs.get("user_id", "")
            safe_log_error(logger, f"[SfpFilemetaTool] Error: {str(e)}", target=target, user_id=user_id, exc_info=True)
            return json.dumps({
                "status": "error",
                "message": f"File Metadata Extractor search failed: {str(e)}",
                "user_id": user_id
            })
