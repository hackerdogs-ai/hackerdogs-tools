"""
holehe Tool for LangChain Agents

Check email registration on 120+ sites
"""

import json
from typing import Optional, List
from langchain.tools import tool, ToolRuntime
from langchain.agents import AgentState
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error, safe_log_debug

logger = setup_logger(__name__, log_file_path="logs/holehe_tool.log")


class HoleheSecurityAgentState(AgentState):
    """Extended agent state for Holehe operations."""
    user_id: str = ""


@tool
def holehe_search(
    runtime: ToolRuntime,
    email: str,
    only_used: bool = True
) -> str:
    """
    Check email registration on 120+ sites using Holehe.
    
    Searches for email address registration across 120+ websites and returns
    which sites the email is registered on.
    
    Args:
        runtime: ToolRuntime instance (automatically injected).
        email: Email address to check (required). Must be a valid email format.
        only_used: If True, only return sites where the email is registered (default: True).
            If False, return all sites checked (both registered and not registered).
    
    Returns:
        JSON array of site results:
        [
            {
                "name": "site_name",
                "exists": true,
                "url": "https://site_name"
            },
            ...
        ]
        - If only_used=True: Only includes sites where email exists
        - If only_used=False: Includes all sites checked (exists: true/false)
        - On error: JSON string with {"status": "error", "message": "..."}
    
    Raises:
        ValueError: If email is invalid
        RuntimeError: If Docker is not available or Holehe execution fails
    
    Note:
        - Holehe checks 120+ sites, which can take several minutes
        - Timeout is set to 5 minutes (300 seconds) to accommodate slow responses
        - Results may vary based on site availability and rate limiting
    """
    try:
        safe_log_info(logger, "[holehe_search] Starting", 
                     email=email, 
                     only_used=only_used)
        
        # Validate inputs
        if not email or not isinstance(email, str) or len(email.strip()) == 0:
            error_msg = "email must be a non-empty string"
            safe_log_error(logger, "[holehe_search] Validation failed", error_msg=error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        email = email.strip()
        
        # Basic email format validation
        if "@" not in email or "." not in email.split("@")[-1]:
            error_msg = "email must be a valid email address format"
            safe_log_error(logger, "[holehe_search] Validation failed", error_msg=error_msg, email=email)
            return json.dumps({"status": "error", "message": error_msg})
        
        safe_log_debug(logger, "[holehe_search] Email validated", email=email)
        
        # Check Docker availability (Docker-only execution)
        safe_log_debug(logger, "[holehe_search] Checking Docker availability")
        from hackerdogs_tools.osint.docker_client import get_docker_client, execute_in_docker
        docker_client = get_docker_client()
        
        if docker_client is None:
            safe_log_debug(logger, "[holehe_search] Docker client is None")
        
        is_available = docker_client.docker_available if docker_client else False
        safe_log_debug(logger, "[holehe_search] Docker availability check", docker_available=is_available)
        
        if not docker_client or not is_available:
            error_msg = (
                "Docker is required for OSINT tools. Setup:\n"
                "1. Build Docker image: cd hackerdogs_tools/osint/docker && docker build -t osint-tools:latest .\n"
                "2. Start container: docker-compose up -d"
            )
            safe_log_error(logger, "[holehe_search] Docker not available", error_msg=error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        # Build command arguments
        # Holehe CLI: holehe <email>
        # Optional: --only-used flag to filter results (handled in parsing, not CLI)
        args = [email]
        
        # Execute in Docker using custom osint-tools container
        # Holehe doesn't have an official Docker image, so it uses the custom container
        # Timeout: 5 minutes (holehe checks 120+ sites, can take time)
        safe_log_info(logger, "[holehe_search] Executing Holehe in Docker", 
                     email=email,
                     timeout=300)
        docker_result = execute_in_docker("holehe", args, timeout=300)
        
        if docker_result["status"] != "success":
            error_msg = f"Holehe failed: {docker_result.get('stderr', docker_result.get('message', 'Unknown error'))}"
            safe_log_error(logger, "[holehe_search] Holehe execution failed", 
                         exc_info=True,
                         error=error_msg,
                         email=email)
            return json.dumps({"status": "error", "message": error_msg})
        
        # Parse output
        stdout = docker_result.get("stdout", "")
        stderr = docker_result.get("stderr", "")
        
        safe_log_debug(logger, "[holehe_search] Parsing Holehe output", 
                      stdout_length=len(stdout),
                      stderr_length=len(stderr))
        
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
                    # Skip email header line (contains @ and common email domains)
                    if '@' in line and any(domain in line.lower() for domain in ['gmail.com', 'hotmail.com', 'live.com', 'yahoo.com', 'outlook.com']):
                        continue
                    # Parse [x] site_name (exists) or [-] site_name (doesn't exist)
                    if line.startswith('[x]'):
                        site_name = line[3:].strip()
                        if site_name:
                            site_result = {
                                "name": site_name,
                                "exists": True,
                                "url": f"https://{site_name}" if not site_name.startswith('http') else site_name
                            }
                            # Always include existing sites
                            results.append(site_result)
                    elif line.startswith('[-]'):
                        site_name = line[3:].strip()
                        if site_name:
                            site_result = {
                                "name": site_name,
                                "exists": False,
                                "url": f"https://{site_name}" if not site_name.startswith('http') else site_name
                            }
                            # Include non-existing sites only if only_used is False
                            if not only_used:
                                results.append(site_result)
                
                # Return results as JSON array
                safe_log_info(logger, "[holehe_search] Complete", 
                            email=email, 
                            sites_found=len(results),
                            only_used=only_used,
                            count=len(results))
                return json.dumps(results, indent=2)
            except Exception as e:
                error_msg = f"Error parsing Holehe output: {str(e)}"
                safe_log_error(logger, "[holehe_search] Parsing failed", 
                             exc_info=True,
                             error=str(e),
                             email=email)
                # Return error instead of falling through
                return json.dumps({"status": "error", "message": error_msg})
        elif stderr:
            # If stdout is empty but stderr has content, log it but return empty results
            safe_log_info(logger, "[holehe_search] Complete - stderr present but no stdout", 
                         email=email,
                         stderr_preview=stderr[:200] if len(stderr) > 200 else stderr)
            return json.dumps([], indent=2)
        
        # If both stdout and stderr are empty, return empty array (no results found)
        safe_log_info(logger, "[holehe_search] Complete - no output, returning empty array", 
                     email=email)
        return json.dumps([], indent=2)
        
    except Exception as e:
        safe_log_error(logger, "[holehe_search] Error", 
                     exc_info=True,
                     error=str(e),
                     email=email if 'email' in locals() else None)
        return json.dumps({"status": "error", "message": f"Holehe search failed: {str(e)}"})
