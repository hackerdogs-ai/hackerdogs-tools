"""
sherlock Tool for LangChain Agents

Username enumeration across 300+ sites
"""

import json
import csv
import io
import tempfile
import os
from pathlib import Path
from typing import Optional, List, Literal
from langchain.tools import tool, ToolRuntime
from langchain.agents import AgentState
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error
from hackerdogs_tools.osint.docker_client import get_docker_client, execute_in_docker

logger = setup_logger(__name__, log_file_path="logs/sherlock_tool.log")


class SherlockSecurityAgentState(AgentState):
    """Extended agent state for Sherlock operations."""
    user_id: str = ""


def _check_docker_available() -> bool:
    """Check if Docker is available."""
    docker_client = get_docker_client()
    if docker_client is None:
        return False
    return docker_client.docker_available


@tool
def sherlock_enum(
    runtime: ToolRuntime,
    usernames: List[str],
    output_format: Literal["csv", "json", "xlsx"] = "csv",
    timeout: int = 60,
    nsfw: bool = False,
    sites: Optional[List[str]] = None
) -> str:
    """
    Username enumeration across 300+ sites using Sherlock.
    
    Searches for usernames across social networks and returns results in specified format.
    
    Args:
        runtime: ToolRuntime instance (automatically injected).
        usernames: List of usernames to search (required).
        output_format: Output format - "csv" (default), "json", or "xlsx".
        timeout: Timeout in seconds for each request (default: 60, range: 1-3600).
        nsfw: Include NSFW sites in search (default: False).
        sites: Optional list of specific sites to search (default: all sites).
    
    Returns:
        JSON string with results including:
        - status: "success" or "error"
        - usernames: List of searched usernames
        - results: Dictionary mapping username to found sites
        - count: Total number of sites found
        - execution_method: "docker" or "official_docker_image"
    """
    try:
        safe_log_info(logger, f"[sherlock_enum] Starting", usernames=usernames, output_format=output_format, timeout=timeout, nsfw=nsfw)
        
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
        
        # Docker-only execution
        if not _check_docker_available():
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
            # CSV output via --output with .csv extension
            temp_dir = tempfile.mkdtemp()
            if len(usernames) == 1:
                output_file_path = os.path.join(temp_dir, f"{usernames[0]}.csv")
                container_csv_path = f"/output/{usernames[0]}.csv"
            else:
                # Multiple usernames - use folderoutput
                output_file_path = temp_dir  # Will contain multiple files
                container_csv_path = "/output"
            volumes.append(f"{temp_dir}:/output")
            if len(usernames) == 1:
                args.extend(["--csv", "--output", container_csv_path])
            else:
                args.extend(["--csv", "--folderoutput", container_csv_path])
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
        
        # Return raw output verbatim - no parsing, no reformatting
        stdout = docker_result.get("stdout", "")
        stderr = docker_result.get("stderr", "")
        
        # For JSON format with single file: return the JSON file content directly, verbatim
        if output_format == "json" and output_file_path:
            # Check if file exists
            if os.path.exists(output_file_path) and os.path.isfile(output_file_path):
                try:
                    with open(output_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        json_content = f.read()
                    # Cleanup temp directory
                    if os.path.exists(os.path.dirname(output_file_path)):
                        try:
                            import shutil
                            shutil.rmtree(os.path.dirname(output_file_path))
                        except Exception:
                            pass
                    # Return JSON file content directly, verbatim - no wrapper
                    safe_log_info(logger, f"[sherlock_enum] Complete - returning JSON file content verbatim", usernames=usernames)
                    return json_content
                except Exception as e:
                    safe_log_error(logger, f"[sherlock_enum] Error reading JSON file: {str(e)}", exc_info=True)
                    # Fall through to check directory
            # If single file doesn't exist, check if it's in the temp directory
            elif output_file_path and os.path.exists(os.path.dirname(output_file_path)):
                # Get the temp directory - since file doesn't exist, use parent directory
                # If output_file_path is a directory, use it directly; otherwise use parent
                if os.path.exists(output_file_path) and os.path.isdir(output_file_path):
                    search_dir = output_file_path
                else:
                    search_dir = os.path.dirname(output_file_path)
                # Look for JSON file in temp directory
                json_file = os.path.join(search_dir, os.path.basename(output_file_path))
                if os.path.exists(json_file) and os.path.isfile(json_file):
                    try:
                        with open(json_file, 'r', encoding='utf-8', errors='ignore') as f:
                            json_content = f.read()
                        # Cleanup temp directory
                        try:
                            import shutil
                            shutil.rmtree(search_dir)
                        except Exception:
                            pass
                        # Return JSON file content directly, verbatim - no wrapper
                        safe_log_info(logger, f"[sherlock_enum] Complete - returning JSON file content verbatim", usernames=usernames)
                        return json_content
                    except Exception as e:
                        safe_log_error(logger, f"[sherlock_enum] Error reading JSON file: {str(e)}", exc_info=True)
                        # Fall through
        
        # For other formats or multiple files: return JSON files directly (no wrapper)
        if output_format == "json" and output_file_path and os.path.exists(output_file_path):
            # Multiple JSON files - return as dictionary mapping username to JSON content
            if os.path.isdir(output_file_path):
                json_results = {}
                try:
                    for file in os.listdir(output_file_path):
                        file_path = os.path.join(output_file_path, file)
                        if os.path.isfile(file_path) and file.endswith('.json'):
                            # Extract username from filename (e.g., "username.json")
                            username = file.replace('.json', '')
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                json_results[username] = f.read()
                except Exception as e:
                    safe_log_error(logger, f"[sherlock_enum] Error reading JSON files: {str(e)}", exc_info=True)
                
                # Cleanup temp directory
                # output_file_path is the directory itself for multiple usernames
                cleanup_dir = output_file_path if os.path.isdir(output_file_path) else os.path.dirname(output_file_path)
                if cleanup_dir and os.path.exists(cleanup_dir):
                    try:
                        import shutil
                        shutil.rmtree(cleanup_dir)
                    except Exception:
                        pass
                
                # Return JSON files as dictionary - no wrapper metadata
                safe_log_info(logger, f"[sherlock_enum] Complete - returning JSON files verbatim", usernames=usernames)
                return json.dumps(json_results, indent=2)
        
        # For CSV format: check for CSV files in output directory
        if output_format == "csv" and output_file_path:
            # Check if CSV file exists
            if os.path.exists(output_file_path) and os.path.isfile(output_file_path):
                try:
                    with open(output_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        csv_content = f.read()
                    # Cleanup temp directory
                    if os.path.exists(os.path.dirname(output_file_path)):
                        try:
                            import shutil
                            shutil.rmtree(os.path.dirname(output_file_path))
                        except Exception:
                            pass
                    # Return CSV file content directly, verbatim - no wrapper
                    safe_log_info(logger, f"[sherlock_enum] Complete - returning CSV file content verbatim", usernames=usernames)
                    return csv_content
                except Exception as e:
                    safe_log_error(logger, f"[sherlock_enum] Error reading CSV file: {str(e)}", exc_info=True)
                    # Fall through to check directory
            # Check if it's a directory with multiple CSV files
            elif os.path.exists(output_file_path) and os.path.isdir(output_file_path):
                csv_results = {}
                try:
                    for file in os.listdir(output_file_path):
                        file_path = os.path.join(output_file_path, file)
                        if os.path.isfile(file_path) and file.endswith('.csv'):
                            # Extract username from filename (e.g., "username.csv")
                            username = file.replace('.csv', '')
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                csv_results[username] = f.read()
                except Exception as e:
                    safe_log_error(logger, f"[sherlock_enum] Error reading CSV files: {str(e)}", exc_info=True)
                
                # Cleanup temp directory
                # output_file_path is the directory itself for multiple usernames
                cleanup_dir = output_file_path if os.path.isdir(output_file_path) else os.path.dirname(output_file_path)
                if cleanup_dir and os.path.exists(cleanup_dir):
                    try:
                        import shutil
                        shutil.rmtree(cleanup_dir)
                    except Exception:
                        pass
                
                # Return CSV files as dictionary - no wrapper metadata
                if csv_results:
                    safe_log_info(logger, f"[sherlock_enum] Complete - returning CSV files verbatim", usernames=usernames)
                    return json.dumps(csv_results, indent=2)
            # Fallback: check temp directory for CSV files
            elif output_file_path:
                # Get the temp directory - check if output_file_path exists and is a directory
                if os.path.exists(output_file_path) and os.path.isdir(output_file_path):
                    search_dir = output_file_path
                else:
                    search_dir = os.path.dirname(output_file_path)
                if os.path.exists(search_dir):
                    try:
                        csv_files = [f for f in os.listdir(search_dir) if f.endswith('.csv')]
                        if csv_files:
                            if len(csv_files) == 1 and len(usernames) == 1:
                                # Single CSV file - return it verbatim
                                csv_file = os.path.join(search_dir, csv_files[0])
                                with open(csv_file, 'r', encoding='utf-8', errors='ignore') as f:
                                    csv_content = f.read()
                                # Cleanup
                                try:
                                    import shutil
                                    shutil.rmtree(search_dir)
                                except Exception:
                                    pass
                                safe_log_info(logger, f"[sherlock_enum] Complete - returning CSV file content verbatim", usernames=usernames)
                                return csv_content
                            else:
                                # Multiple CSV files - return as dict
                                csv_results = {}
                                for csv_file in csv_files:
                                    file_path = os.path.join(search_dir, csv_file)
                                    username = csv_file.replace('.csv', '')
                                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                        csv_results[username] = f.read()
                                # Cleanup
                                try:
                                    import shutil
                                    shutil.rmtree(search_dir)
                                except Exception:
                                    pass
                                safe_log_info(logger, f"[sherlock_enum] Complete - returning CSV files verbatim", usernames=usernames)
                                return json.dumps(csv_results, indent=2)
                    except Exception as e:
                        safe_log_error(logger, f"[sherlock_enum] Error checking temp directory for CSV: {str(e)}", exc_info=True)
        
        # For JSON format: check if JSON files were created in temp directory even if path check failed
        if output_format == "json" and output_file_path:
            # Get the temp directory - check if output_file_path exists and is a directory
            if os.path.exists(output_file_path) and os.path.isdir(output_file_path):
                search_dir = output_file_path
            else:
                search_dir = os.path.dirname(output_file_path)
            if search_dir and os.path.exists(search_dir):
                # Look for any JSON files in the temp directory
                try:
                    json_files = [f for f in os.listdir(search_dir) if f.endswith('.json')]
                    if json_files:
                        if len(json_files) == 1 and len(usernames) == 1:
                            # Single JSON file - return it verbatim
                            json_file = os.path.join(search_dir, json_files[0])
                            with open(json_file, 'r', encoding='utf-8', errors='ignore') as f:
                                json_content = f.read()
                            # Cleanup
                            try:
                                import shutil
                                shutil.rmtree(search_dir)
                            except Exception:
                                pass
                            safe_log_info(logger, f"[sherlock_enum] Complete - returning JSON file content verbatim", usernames=usernames)
                            return json_content
                        else:
                            # Multiple JSON files - return as dict
                            json_results = {}
                            for json_file in json_files:
                                file_path = os.path.join(search_dir, json_file)
                                username = json_file.replace('.json', '')
                                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                    json_results[username] = f.read()
                            # Cleanup
                            try:
                                import shutil
                                shutil.rmtree(search_dir)
                            except Exception:
                                pass
                            safe_log_info(logger, f"[sherlock_enum] Complete - returning JSON files verbatim", usernames=usernames)
                            return json.dumps(json_results, indent=2)
                except Exception as e:
                    safe_log_error(logger, f"[sherlock_enum] Error checking temp directory: {str(e)}", exc_info=True)
        
        # Cleanup temp directory
        if output_file_path:
            # output_file_path might be a directory (for multiple usernames) or a file path
            cleanup_dir = output_file_path if os.path.isdir(output_file_path) else os.path.dirname(output_file_path)
            if cleanup_dir and os.path.exists(cleanup_dir):
                try:
                    import shutil
                    shutil.rmtree(cleanup_dir)
                except Exception:
                    pass
        
        # Return stdout/stderr verbatim - no wrapper
        safe_log_info(logger, f"[sherlock_enum] Complete - returning stdout verbatim", usernames=usernames)
        return stdout if stdout else stderr

    except Exception as e:
        safe_log_error(logger, f"[sherlock_enum] Error: {str(e)}", exc_info=True)
        return json.dumps({"status": "error", "message": f"Sherlock enumeration failed: {str(e)}"})
