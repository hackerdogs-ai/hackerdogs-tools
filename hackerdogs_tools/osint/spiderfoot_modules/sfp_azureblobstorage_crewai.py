"""
Azure Blob Finder Tool for CrewAI Agents

Search for potential Azure blobs associated with the target and attempt to list their contents.
Data Source: https://azure.microsoft.com/en-in/services/storage/blobs/
"""

import json
import os
from typing import Any, Optional, Dict, List
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error

logger = setup_logger(__name__, log_file_path="logs/spiderfoot_azureblobstorage_tool.log")




class SfpAzureblobstorageToolSchema(BaseModel):
    """Input schema for Azure Blob FinderTool."""
    target: str = Field(..., description="Target to investigate (DOMAIN_NAME, LINKED_URL_EXTERNAL)")
    suffixes: Optional[str] = Field(
        default="test,dev,web,beta,bucket,space,files,content,data,prod,staging,production,stage,app,media,development,-test,-dev,-web,-beta,-bucket,-space,-files,-content,-data,-prod,-staging,-production,-stage,-app,-media,-development",
        description="List of suffixes to append to domains tried as blob storage names"
    )


class SfpAzureblobstorageTool(BaseTool):
    """Tool for Search for potential Azure blobs associated with the target and attempt to list their contents.."""
    
    name: str = "Azure Blob Finder"
    description: str = (
        "Search for potential Azure blobs associated with the target and attempt to list their contents."
        "\n\nUse Cases: Footprint, Passive"
        "\nCategories: Crawling and Scanning"
    )
    args_schema: type[BaseModel] = SfpAzureblobstorageToolSchema
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
    
    def _run(
        self,
        target: str,
        suffixes: Optional[str] = "test,dev,web,beta,bucket,space,files,content,data,prod,staging,production,stage,app,media,development,-test,-dev,-web,-beta,-bucket,-space,-files,-content,-data,-prod,-staging,-production,-stage,-app,-media,-development",
        **kwargs: Any
    ) -> str:
        """Execute Azure Blob Finder."""
        try:
            safe_log_info(logger, f"[SfpAzureblobstorageTool] Starting", target=target)
            
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
                implement_azureblobstorage
            )
            
            # Build parameters for the implementation function
            implementation_params = {
                "target": target,
                "suffixes": suffixes,
            }
            
            # Execute migrated implementation
            implementation_result = implement_azureblobstorage(**implementation_params)
            
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
                "module": "sfp_azureblobstorage",
                "module_name": "Azure Blob Finder",
                "target": target,
                "raw_response": result_data,
                "user_id": user_id,
                "note": "Raw output from Azure Blob Finder tool - migrated standalone implementation"
            }
            
            safe_log_info(logger, f"[SfpAzureblobstorageTool] Complete", target=target, user_id=user_id)
            return json.dumps(result, indent=2)
            
        except Exception as e:
            target = kwargs.get("target", "unknown")
            user_id = kwargs.get("user_id", "")
            safe_log_error(logger, f"[SfpAzureblobstorageTool] Error: {str(e)}", target=target, user_id=user_id, exc_info=True)
            return json.dumps({
                "status": "error",
                "message": f"Azure Blob Finder search failed: {str(e)}",
                "user_id": user_id
            })
