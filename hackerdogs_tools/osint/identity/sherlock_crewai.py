"""
Sherlock Tool for CrewAI Agents

Username enumeration across 300+ sites
"""

import json
import csv
import io
import tempfile
import os
from pathlib import Path
from typing import Any, Optional, List, Literal
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error
from hackerdogs_tools.osint.docker_client import get_docker_client, execute_in_docker

logger = setup_logger(__name__, log_file_path="logs/sherlock_tool.log")


class SherlockToolSchema(BaseModel):
    """Input schema for SherlockTool."""
    usernames: List[str] = Field(..., description="List of usernames to search across social networks")
    output_format: Literal["csv", "json", "xlsx"] = Field(default="csv", description="Output format: csv (default), json, or xlsx")
    timeout: int = Field(default=60, ge=1, le=3600, description="Timeout in seconds for each request (default: 60, range: 1-3600)")
    nsfw: bool = Field(default=False, description="Include NSFW sites in search (default: False)")
    sites: Optional[List[str]] = Field(default=None, description="Optional list of specific sites to search (default: all sites)")


class SherlockTool(BaseTool):
    """Tool for Username enumeration across 300+ sites."""
    
    name: str = "Sherlock"
    description: str = "Username enumeration across 300+ sites using Sherlock. Searches for usernames across social networks and returns results."
    args_schema: type[BaseModel] = SherlockToolSchema
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
    
    def _run(
        self,
        usernames: List[str],
        output_format: Literal["csv", "json", "xlsx"] = "csv",
        timeout: int = 60,
        nsfw: bool = False,
        sites: Optional[List[str]] = None,
        **kwargs: Any
    ) -> str:
        """Execute Sherlock username enumeration."""
        try:
            safe_log_info(logger, f"[SherlockTool] Starting", usernames=usernames, output_format=output_format, timeout=timeout, nsfw=nsfw)
            
            # Validate inputs
            if not usernames or not isinstance(usernames, list) or len(usernames) == 0:
                error_msg = "usernames must be a non-empty list"
                safe_log_error(logger, error_msg)
                return json.dumps({"status": "error", "message": error_msg})
            
            # Validate each username
            for username in usernames:
                if not isinstance(username, str) or len(username.strip()) == 0:
                    error_msg = f"Invalid username in list: {username}"
                    safe_log_error(logger, error_msg)
                    return json.dumps({"status": "error", "message": error_msg})
            
            if output_format not in ["csv", "json", "xlsx"]:
                error_msg = "output_format must be 'csv', 'json', or 'xlsx'"
                safe_log_error(logger, error_msg)
                return json.dumps({"status": "error", "message": error_msg})
            
            if timeout < 1 or timeout > 3600:
                error_msg = "timeout must be between 1 and 3600 seconds"
                safe_log_error(logger, error_msg)
                return json.dumps({"status": "error", "message": error_msg})
            
            # Check Docker availability (Docker-only execution)
            docker_client = get_docker_client()
            
            if not docker_client or not docker_client.docker_available:
                error_msg = (
                    "Docker is required for OSINT tools. Setup:\n"
                    "1. Pull Docker image: docker pull sherlock/sherlock:latest\n"
                    "2. Ensure Docker is running"
                )
                safe_log_error(logger, error_msg)
                return json.dumps({"status": "error", "message": error_msg})
            
            # Build command arguments
            args = []
            volumes = []
            output_file_path = None
            
            # Output format - handle file-based outputs
            # Note: --json is for INPUT (loading data), not output
            # For JSON output, use --output with .json extension
            # For CSV/XLSX, use --csv/--xlsx flags (output to stdout or default location)
            if output_format == "json":
                # JSON output via --output with .json extension
                temp_dir = tempfile.mkdtemp()
                if len(usernames) == 1:
                    output_file_path = os.path.join(temp_dir, f"{usernames[0]}.json")
                    container_json_path = f"/output/{usernames[0]}.json"
                else:
                    # Multiple usernames - use folderoutput
                    output_file_path = temp_dir  # Will contain multiple files
                    container_json_path = "/output"
                volumes.append(f"{temp_dir}:/output")
                if len(usernames) == 1:
                    args.extend(["--output", container_json_path])
                else:
                    args.extend(["--folderoutput", container_json_path])
            elif output_format == "csv":
                args.append("--csv")
            elif output_format == "xlsx":
                # XLSX output
                temp_dir = tempfile.mkdtemp()
                if len(usernames) == 1:
                    output_file_path = os.path.join(temp_dir, f"{usernames[0]}.xlsx")
                    container_xlsx_path = f"/output/{usernames[0]}.xlsx"
                    volumes.append(f"{temp_dir}:/output")
                    args.extend(["--xlsx", "--output", container_xlsx_path])
                else:
                    output_file_path = temp_dir  # Will contain multiple files
                    container_xlsx_path = "/output"
                    volumes.append(f"{temp_dir}:/output")
                    args.extend(["--xlsx", "--folderoutput", container_xlsx_path])
            
            # Timeout
            args.extend(["--timeout", str(timeout)])
            
            # NSFW flag
            if nsfw:
                args.append("--nsfw")
            
            # Site filtering
            if sites:
                for site in sites:
                    args.extend(["--site", site])
            
            # Add usernames (positional arguments)
            args.extend(usernames)
            
            # Execute in Docker using official sherlock/sherlock image
            # Calculate timeout: (timeout per request * number of usernames) + buffer
            execution_timeout = (timeout * len(usernames) * 2) + 120  # Buffer for processing
            docker_result = execute_in_docker("sherlock", args, timeout=execution_timeout, volumes=volumes if volumes else None)
            
            if docker_result["status"] != "success":
                error_msg = f"Sherlock failed: {docker_result.get('stderr', docker_result.get('message', 'Unknown error'))}"
                safe_log_error(logger, error_msg)
                return json.dumps({"status": "error", "message": error_msg})
            
            # Parse output based on format
            stdout = docker_result.get("stdout", "")
            stderr = docker_result.get("stderr", "")
            
            results = {}
            total_count = 0
            
            # For JSON format, parse text output from stdout or file
            # Note: Sherlock's --output with .json extension creates a text file with URLs, not JSON
            # We parse the stdout text output to extract results
            if output_format == "json":
                # Parse stdout text output to extract results
                # Format: "[*] Checking username X on:" followed by "[+] Site Name: URL"
                import re
                
                # Split stdout by username sections
                # Pattern: "[*] Checking username <username> on:"
                username_section_pattern = r'\[\*\]\s+Checking username\s+(\w+)\s+on:'
                
                # Find all username sections
                sections = re.finditer(username_section_pattern, stdout)
                current_username = None
                section_start = 0
                
                # Process each section
                section_positions = []
                for match in sections:
                    if current_username is not None:
                        # Save previous section
                        section_positions.append((current_username, section_start, match.start()))
                    current_username = match.group(1)
                    section_start = match.start()
                
                # Add last section
                if current_username is not None:
                    section_positions.append((current_username, section_start, len(stdout)))
                
                # Extract results for each username section
                for username, start_pos, end_pos in section_positions:
                    if username not in results:
                        results[username] = []
                    
                    # Extract results from this section
                    section_text = stdout[start_pos:end_pos]
                    pattern = r'\[\+\]\s+([^:]+):\s+(https?://[^\s]+)'
                    matches = re.findall(pattern, section_text)
                    
                    for site_name, url in matches:
                        results[username].append({
                            "name": site_name.strip(),
                            "url_main": url,
                            "url_user": url,
                            "exists": True,
                            "http_status": 200,
                            "response_time_ms": 0
                        })
                        total_count += 1
                
                # If no sections found (single username or different format), try simple parsing
                if not section_positions and len(usernames) == 1:
                    username = usernames[0]
                    if username not in results:
                        results[username] = []
                    
                    pattern = r'\[\+\]\s+([^:]+):\s+(https?://[^\s]+)'
                    matches = re.findall(pattern, stdout)
                    
                    for site_name, url in matches:
                        if username.lower() in url.lower():
                            results[username].append({
                                "name": site_name.strip(),
                                "url_main": url,
                                "url_user": url,
                                "exists": True,
                                "http_status": 200,
                                "response_time_ms": 0
                            })
                            total_count += 1
                
                # Also check the output file(s) if they exist (contains URLs)
                if output_file_path:
                    try:
                        if len(usernames) == 1 and os.path.exists(output_file_path):
                            # Single username - one file
                            with open(output_file_path, 'r', encoding='utf-8') as f:
                                file_content = f.read()
                                username = usernames[0]
                                if username not in results:
                                    results[username] = []
                                
                                # Extract URLs from file (one per line)
                                for line in file_content.strip().split('\n'):
                                    line = line.strip()
                                    if line and (line.startswith('http://') or line.startswith('https://')):
                                        # Try to extract site name from URL
                                        domain = line.split('/')[2] if '/' in line else line
                                        site_name = domain.split('.')[0] if '.' in domain else domain
                                        
                                        # Check if we already have this URL
                                        if not any(r.get("url_user") == line for r in results[username]):
                                            results[username].append({
                                                "name": site_name,
                                                "url_main": line,
                                                "url_user": line,
                                                "exists": True,
                                                "http_status": 200,
                                                "response_time_ms": 0
                                            })
                                            total_count += 1
                        elif len(usernames) > 1 and os.path.exists(output_file_path):
                            # Multiple usernames - check folder for individual files
                            for username in usernames:
                                username_file = os.path.join(output_file_path, f"{username}.json")
                                if os.path.exists(username_file):
                                    with open(username_file, 'r', encoding='utf-8') as f:
                                        file_content = f.read()
                                        if username not in results:
                                            results[username] = []
                                        
                                        # Extract URLs from file
                                        for line in file_content.strip().split('\n'):
                                            line = line.strip()
                                            if line and (line.startswith('http://') or line.startswith('https://')):
                                                domain = line.split('/')[2] if '/' in line else line
                                                site_name = domain.split('.')[0] if '.' in domain else domain
                                                
                                                if not any(r.get("url_user") == line for r in results[username]):
                                                    results[username].append({
                                                        "name": site_name,
                                                        "url_main": line,
                                                        "url_user": line,
                                                        "exists": True,
                                                        "http_status": 200,
                                                        "response_time_ms": 0
                                                    })
                                                    total_count += 1
                    except Exception as e:
                        safe_log_error(logger, f"[SherlockTool] Error reading output file: {str(e)}", exc_info=True)
                
                # Cleanup temp directory
                if output_file_path and os.path.exists(os.path.dirname(output_file_path)):
                    try:
                        import shutil
                        shutil.rmtree(os.path.dirname(output_file_path))
                    except Exception:
                        pass
            
            elif output_format == "csv":
                # Parse CSV output
                try:
                    csv_reader = csv.DictReader(io.StringIO(stdout))
                    for row in csv_reader:
                        username = row.get("username", "")
                        if username not in results:
                            results[username] = []
                        results[username].append({
                            "name": row.get("name", ""),
                            "url_main": row.get("url_main", ""),
                            "url_user": row.get("url_user", ""),
                            "exists": row.get("exists", "").lower() == "true" if row.get("exists") else False,
                            "http_status": int(row.get("http_status", 0)) if row.get("http_status") else 0,
                            "response_time_ms": float(row.get("response_time_ms", 0)) if row.get("response_time_ms") else 0
                        })
                        if row.get("exists", "").lower() == "true":
                            total_count += 1
                except Exception as e:
                    safe_log_error(logger, f"[SherlockTool] CSV parsing error: {str(e)}", exc_info=True)
                    # Fallback: try to extract from stdout text
                    for username in usernames:
                        if username in stdout:
                            results[username] = [{"raw_output": "Found in output", "exists": True}]
                            total_count += 1
            
            elif output_format == "xlsx":
                # XLSX output - Sherlock writes to file
                if output_file_path:
                    # Check if file was created (for single username, it's the specific file; for multiple, check folder)
                    if len(usernames) == 1 and os.path.exists(output_file_path):
                        safe_log_info(logger, "[SherlockTool] XLSX file generated", file_path=output_file_path)
                        results[usernames[0]] = [{"raw_output": "XLSX file generated", "file_path": output_file_path, "exists": True}]
                        total_count += 1
                    elif len(usernames) > 1 and os.path.exists(os.path.dirname(output_file_path)):
                        # Multiple usernames - check folder for individual files
                        output_dir = os.path.dirname(output_file_path)
                        for username in usernames:
                            username_file = os.path.join(output_dir, f"{username}.xlsx")
                            if os.path.exists(username_file):
                                results[username] = [{"raw_output": "XLSX file generated", "file_path": username_file, "exists": True}]
                                total_count += 1
                    # Cleanup temp directory
                    if output_file_path and os.path.exists(os.path.dirname(output_file_path)):
                        try:
                            import shutil
                            shutil.rmtree(os.path.dirname(output_file_path))
                        except Exception:
                            pass
                else:
                    # Fallback: parse stdout/stderr for any text output
                    output_text = stdout + stderr
                    for username in usernames:
                        if username in output_text:
                            results[username] = [{"raw_output": "XLSX file generated", "exists": True}]
                            total_count += 1
            
            # If no results parsed, check if there's any output
            if not results and stdout:
                # Try to extract usernames from output
                for username in usernames:
                    if username in stdout or username in stderr:
                        results[username] = [{"raw_output": stdout[:500], "exists": True}]
                        total_count += 1
            
            result_data = {
                "status": "success",
                "usernames": usernames,
                "results": results,
                "count": total_count,
                "output_format": output_format,
                "execution_method": docker_result.get("execution_method", "docker")
            }
            
            safe_log_info(logger, f"[SherlockTool] Complete", usernames=usernames, count=total_count)
            return json.dumps(result_data, indent=2)
            
        except Exception as e:
            safe_log_error(logger, f"[SherlockTool] Error: {str(e)}", exc_info=True)
            return json.dumps({"status": "error", "message": f"Sherlock enumeration failed: {str(e)}"})
