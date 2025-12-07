"""
Maigret Tool for CrewAI Agents

Advanced username search with metadata extraction across 3000+ sites
"""

import json
import tempfile
import os
import shutil
from typing import Any, Optional, List, Literal
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error
from hackerdogs_tools.osint.docker_client import get_docker_client, execute_in_docker

logger = setup_logger(__name__, log_file_path="logs/maigret_tool.log")


def _check_docker_available() -> bool:
    """Check if Docker is available."""
    docker_client = get_docker_client()
    if docker_client is None:
        return False
    return docker_client.docker_available


class MaigretToolSchema(BaseModel):
    """Input schema for MaigretTool."""
    username: str = Field(..., description="Username to search (can be a single username or comma-separated list)")
    report_format: Literal["txt", "csv", "html", "xmind", "pdf", "graph", "json"] = Field(default="json", description="Report format")
    json_type: Literal["simple", "ndjson"] = Field(default="simple", description="JSON report type (only used when report_format='json')")
    timeout: int = Field(default=30, ge=1, le=300, description="Time in seconds to wait for response to requests")
    sites: Optional[List[str]] = Field(default=None, description="Optional list of specific site names to limit analysis to")


class MaigretTool(BaseTool):
    """Tool for Advanced username search with metadata."""
    
    name: str = "Maigret"
    description: str = "Advanced username search with metadata extraction across 3000+ sites using Maigret"
    args_schema: type[BaseModel] = MaigretToolSchema
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
    
    def _run(
        self,
        username: str,
        report_format: Literal["txt", "csv", "html", "xmind", "pdf", "graph", "json"] = "json",
        json_type: Literal["simple", "ndjson"] = "simple",
        timeout: int = 30,
        sites: Optional[List[str]] = None,
        **kwargs: Any
    ) -> str:
        """Execute Maigret."""
        temp_dir = None
        volumes = []
        
        try:
            # Parse username - can be single or comma-separated
            if ',' in username:
                usernames = [u.strip() for u in username.split(',') if u.strip()]
            else:
                usernames = [username.strip()] if username.strip() else []
            
            if not usernames:
                error_msg = "username must be provided"
                safe_log_error(logger, error_msg)
                return json.dumps({"status": "error", "message": error_msg})
            
            safe_log_info(logger, f"[MaigretTool] Starting", usernames=usernames, report_format=report_format, timeout=timeout)
            
            # Validate inputs
            if report_format not in ["txt", "csv", "html", "xmind", "pdf", "graph", "json"]:
                error_msg = "report_format must be one of: txt, csv, html, xmind, pdf, graph, json"
                safe_log_error(logger, error_msg)
                return json.dumps({"status": "error", "message": error_msg})
            
            if json_type not in ["simple", "ndjson"]:
                error_msg = "json_type must be 'simple' or 'ndjson'"
                safe_log_error(logger, error_msg)
                return json.dumps({"status": "error", "message": error_msg})
            
            if not (1 <= timeout <= 300):
                error_msg = "timeout must be between 1 and 300 seconds"
                safe_log_error(logger, error_msg)
                return json.dumps({"status": "error", "message": error_msg})
            
            # Docker-only execution
            if not _check_docker_available():
                error_msg = (
                    "Docker is required for OSINT tools. Setup:\n"
                    "1. Pull Docker image: docker pull soxoj/maigret:latest\n"
                    "2. Ensure Docker is running"
                )
                safe_log_error(logger, error_msg)
                return json.dumps({"status": "error", "message": error_msg})
            
            # Build command arguments
            args = []
            
            # Timeout
            args.extend(["--timeout", str(timeout)])
            
            # Max connections (default 100)
            args.extend(["-n", "100"])
            
            # Report formats
            if report_format == "txt":
                args.append("-T")
            elif report_format == "csv":
                args.append("-C")
            elif report_format == "html":
                args.append("-H")
            elif report_format == "xmind":
                args.append("-X")
            elif report_format == "pdf":
                args.append("-P")
            elif report_format == "graph":
                args.append("-G")
            elif report_format == "json":
                args.extend(["-J", json_type])
            
            # Site filtering
            if sites:
                for site in sites:
                    args.extend(["--site", site])
            
            # Setup output directory for reports
            if report_format in ["txt", "csv", "html", "xmind", "pdf", "graph", "json"]:
                temp_dir = tempfile.mkdtemp()
                container_output_path = "/app/reports"
                volumes.append(f"{temp_dir}:{container_output_path}")
                args.extend(["--folderoutput", container_output_path])
            
            # Add usernames (positional arguments)
            args.extend(usernames)
            
            # Execute in Docker using official soxoj/maigret image
            # Calculate timeout: (timeout per request * number of usernames * sites) + buffer
            estimated_sites = 500  # Default top sites
            execution_timeout = (timeout * estimated_sites / 100) + 300  # Buffer
            execution_timeout = min(execution_timeout, 3600)  # Cap at 1 hour
            
            docker_result = execute_in_docker("maigret", args, timeout=int(execution_timeout), volumes=volumes if volumes else None)
            
            if docker_result["status"] != "success":
                error_msg = f"Maigret failed: {docker_result.get('stderr', docker_result.get('message', 'Unknown error'))}"
                safe_log_error(logger, error_msg)
                return json.dumps({"status": "error", "message": error_msg})
            
            # Parse output
            stdout = docker_result.get("stdout", "")
            stderr = docker_result.get("stderr", "")
            
            # For JSON format with single username: return the JSON file content directly, verbatim
            if report_format == "json" and temp_dir and len(usernames) == 1:
                try:
                    username = usernames[0]
                    json_file = None
                    # Try Maigret's naming pattern: report_{username}_{type}.json
                    if json_type == "simple":
                        json_file = os.path.join(temp_dir, f"report_{username}_simple.json")
                        # Fallback to old naming
                        if not os.path.exists(json_file):
                            json_file = os.path.join(temp_dir, f"{username}.json")
                    else:  # ndjson
                        json_file = os.path.join(temp_dir, f"report_{username}_ndjson.json")
                        # Fallback to old naming
                        if not os.path.exists(json_file):
                            json_file = os.path.join(temp_dir, f"{username}.ndjson")
                    
                    if json_file and os.path.exists(json_file):
                        # Read raw JSON file and return directly, verbatim - no wrapper
                        with open(json_file, 'r', encoding='utf-8') as f:
                            json_content = f.read()
                        # Cleanup temp directory
                        if os.path.exists(temp_dir):
                            try:
                                shutil.rmtree(temp_dir)
                            except Exception:
                                pass
                        # Return JSON file content directly, verbatim - no wrapper
                        safe_log_info(logger, f"[MaigretTool] Complete - returning JSON file content verbatim", usernames=usernames)
                        return json_content
                except Exception as e:
                    safe_log_error(logger, f"[MaigretTool] Error reading JSON file: {str(e)}", exc_info=True)
                    # Fall through to wrapper format
            
            # For multiple usernames: return JSON files directly as dictionary (no wrapper)
            if report_format == "json" and temp_dir:
                json_results = {}
                try:
                    # Look for JSON files in the output directory
                    for username in usernames:
                        json_file = None
                        if json_type == "simple":
                            json_file = os.path.join(temp_dir, f"report_{username}_simple.json")
                            if not os.path.exists(json_file):
                                json_file = os.path.join(temp_dir, f"{username}.json")
                        else:  # ndjson
                            json_file = os.path.join(temp_dir, f"report_{username}_ndjson.json")
                            if not os.path.exists(json_file):
                                json_file = os.path.join(temp_dir, f"{username}.ndjson")
                        
                        if os.path.exists(json_file):
                            # Read raw JSON file and return as-is (verbatim, no parsing)
                            with open(json_file, 'r', encoding='utf-8') as f:
                                json_results[username] = f.read()  # Return as raw string, not parsed
                except Exception as e:
                    safe_log_error(logger, f"[MaigretTool] Error reading JSON files: {str(e)}", exc_info=True)
                
                # Cleanup temp directory
                if os.path.exists(temp_dir):
                    try:
                        shutil.rmtree(temp_dir)
                    except Exception:
                        pass
                
                # Return JSON files as dictionary mapping username to JSON content - no wrapper
                if json_results:
                    safe_log_info(logger, f"[MaigretTool] Complete - returning JSON files verbatim", usernames=usernames)
                    return json.dumps(json_results, indent=2)
            
            # For CSV format: check for CSV files in output directory
            if report_format == "csv" and temp_dir and os.path.exists(temp_dir):
                csv_results = {}
                try:
                    for username in usernames:
                        csv_file = os.path.join(temp_dir, f"report_{username}.csv")
                        if not os.path.exists(csv_file):
                            csv_file = os.path.join(temp_dir, f"{username}.csv")
                        
                        if os.path.exists(csv_file):
                            with open(csv_file, 'r', encoding='utf-8') as f:
                                csv_results[username] = f.read()
                except Exception as e:
                    safe_log_error(logger, f"[MaigretTool] Error reading CSV files: {str(e)}", exc_info=True)
                
                # Cleanup temp directory
                if os.path.exists(temp_dir):
                    try:
                        shutil.rmtree(temp_dir)
                    except Exception:
                        pass
                
                # Return CSV files as dictionary mapping username to CSV content - no wrapper
                if csv_results:
                    if len(csv_results) == 1 and len(usernames) == 1:
                        # Single CSV file - return it verbatim
                        safe_log_info(logger, f"[MaigretTool] Complete - returning CSV file content verbatim", usernames=usernames)
                        return list(csv_results.values())[0]
                    else:
                        # Multiple CSV files - return as dict
                        safe_log_info(logger, f"[MaigretTool] Complete - returning CSV files verbatim", usernames=usernames)
                        return json.dumps(csv_results, indent=2)
            
            # For other non-JSON formats or if files not found: return stdout/stderr verbatim
            # Cleanup temp directory
            if temp_dir and os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                except Exception:
                    pass
            
            # Return stdout/stderr verbatim - no wrapper
            safe_log_info(logger, f"[MaigretTool] Complete - returning stdout verbatim", usernames=usernames)
            return stdout if stdout else stderr
            
        except Exception as e:
            safe_log_error(logger, f"[MaigretTool] Error: {str(e)}", exc_info=True)
            return json.dumps({"status": "error", "message": f"Maigret search failed: {str(e)}"})
        finally:
            # Cleanup temp directory
            if temp_dir and os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                    safe_log_info(logger, f"[MaigretTool] Cleaned up temporary directory: {temp_dir}")
                except Exception as e:
                    safe_log_error(logger, f"[MaigretTool] Error cleaning up temporary directory {temp_dir}: {str(e)}", exc_info=True)
