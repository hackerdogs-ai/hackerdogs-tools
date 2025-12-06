"""
Holehe Tool for CrewAI Agents

Check email registration on 120+ sites
"""

import json
from typing import Any, Optional, List
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error

logger = setup_logger(__name__, log_file_path="logs/holehe_tool.log")


class HoleheToolSchema(BaseModel):
    """Input schema for HoleheTool."""
    email: str = Field(..., description="Email address to check")
    only_used: bool = Field(default=True, description="Only show sites where email is used")


class HoleheTool(BaseTool):
    """Tool for Check email registration on 120+ sites."""
    
    name: str = "Holehe"
    description: str = "Check email registration on 120+ sites"
    args_schema: type[BaseModel] = HoleheToolSchema
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
    
    def _run(
        self,
        email: str,
        only_used: bool = True,
        **kwargs: Any
    ) -> str:
        """Execute Holehe email check."""
        try:
            safe_log_info(logger, f"[HoleheTool] Starting", email=email, only_used=only_used)
            
            # Validate inputs
            if not email or not isinstance(email, str) or "@" not in email:
                error_msg = "Invalid email address provided"
                safe_log_error(logger, error_msg)
                return json.dumps({"status": "error", "message": error_msg})
            
            # Check Docker availability (Docker-only execution)
            from hackerdogs_tools.osint.docker_client import get_docker_client, execute_in_docker
            docker_client = get_docker_client()
            
            if not docker_client or not docker_client.docker_available:
                error_msg = (
                    "Docker is required for OSINT tools. Setup:\n"
                    "1. Build Docker image: cd hackerdogs_tools/osint/docker && docker build -t osint-tools:latest .\n"
                    "2. Start container: docker-compose up -d"
                )
                safe_log_error(logger, error_msg)
                return json.dumps({"status": "error", "message": error_msg})
            
            # Build command arguments
            # Holehe CLI: holehe <email>
            # Optional: --only-used flag to filter results
            args = [email]
            
            # Execute in Docker using custom osint-tools container
            # Holehe doesn't have an official Docker image, so it uses the custom container
            # Timeout: 5 minutes (holehe checks 120+ sites, can take time)
            docker_result = execute_in_docker("holehe", args, timeout=300)
            
            if docker_result["status"] != "success":
                error_msg = f"Holehe failed: {docker_result.get('stderr', docker_result.get('message', 'Unknown error'))}"
                safe_log_error(logger, error_msg)
                return json.dumps({"status": "error", "message": error_msg})
            
            # Parse output
            stdout = docker_result.get("stdout", "")
            stderr = docker_result.get("stderr", "")
            
            # Holehe outputs text format: [x] site_name (exists) or [-] site_name (doesn't exist)
            # Parse text output and convert to JSON
            if stdout:
                try:
                    results = []
                    for line in stdout.strip().split('\n'):
                        line = line.strip()
                        if not line:
                            continue
                        # Skip header lines (lines with asterisks or dashes)
                        if line.startswith('*') or (line.startswith('-') and len(line) > 20):
                            continue
                        # Skip email header line
                        if '@' in line and ('gmail.com' in line.lower() or 'hotmail.com' in line.lower() or 'live.com' in line.lower()):
                            continue
                        # Parse [x] site_name or [-] site_name
                        if line.startswith('[x]'):
                            site_name = line[3:].strip()
                            if site_name:
                                site_result = {
                                    "name": site_name,
                                    "exists": True,
                                    "url": f"https://{site_name}" if not site_name.startswith('http') else site_name
                                }
                                if not only_used or site_result.get("exists", False):
                                    results.append(site_result)
                        elif line.startswith('[-]'):
                            site_name = line[3:].strip()
                            if site_name:
                                site_result = {
                                    "name": site_name,
                                    "exists": False,
                                    "url": f"https://{site_name}" if not site_name.startswith('http') else site_name
                                }
                                if not only_used:  # Include non-existing sites if only_used is False
                                    results.append(site_result)
                    
                    # Return results as JSON array
                    safe_log_info(logger, f"[HoleheTool] Complete", email=email, sites_found=len(results))
                    return json.dumps(results, indent=2)
                except Exception as e:
                    safe_log_error(logger, f"[HoleheTool] Error parsing output: {str(e)}", exc_info=True)
                    # Fall through to return raw output
            elif stderr:
                # If stdout is empty but stderr has content, return it
                safe_log_info(logger, f"[HoleheTool] Complete - returning stderr", email=email)
                return stderr
            
            # If both stdout and stderr are empty, return empty array (no results found)
            safe_log_info(logger, f"[HoleheTool] Complete - no output, returning empty array", email=email)
            return json.dumps([], indent=2)
            
        except Exception as e:
            safe_log_error(logger, f"[HoleheTool] Error: {str(e)}", exc_info=True)
            return json.dumps({"status": "error", "message": f"Holehe check failed: {str(e)}"})
