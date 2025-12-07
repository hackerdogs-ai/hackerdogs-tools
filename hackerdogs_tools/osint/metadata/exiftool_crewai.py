"""
ExifTool Tool for CrewAI Agents

Extract metadata from images/PDFs
"""

import json
import subprocess
import shutil
from typing import Any, Optional, List
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error

logger = setup_logger(__name__, log_file_path="logs/exiftool_tool.log")


class ExifToolToolSchema(BaseModel):
    """Input schema for ExifToolTool."""
    file_path: str = Field(..., description="Path to image, PDF, or other file for metadata extraction. File must be accessible via Docker volume mount.")
    extract_gps: bool = Field(default=True, description="If True, prioritize GPS-related metadata extraction (GPS coordinates, location data)")
    extract_author: bool = Field(default=True, description="If True, prioritize author/creator metadata extraction (Author, Creator, Producer fields)")
    output_format: str = Field(default="json", description="Output format: 'json' (default) for structured JSON, or 'text' for human-readable text")


class ExifToolTool(BaseTool):
    """Tool for Extract metadata from images/PDFs."""
    
    name: str = "ExifTool"
    description: str = (
        "Extract metadata from images, PDFs, and other files using ExifTool. "
        "Use cases: 1) Geospatial Intelligence - Extract GPS coordinates from photos, "
        "2) Device Fingerprinting - Identify camera/device make/model/software, "
        "3) Document Attribution - Extract author/creator from PDFs, "
        "4) Timeline Reconstruction - Extract timestamps, "
        "5) Image Authenticity - Detect editing software and manipulation history. "
        "Returns JSON with metadata fields like GPS coordinates, author, device info, timestamps."
    )
    args_schema: type[BaseModel] = ExifToolToolSchema
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        # Add validation if needed
        # if not shutil.which("exiftool"):
        #     raise ValueError("ExifTool not found. Please install it.")
    
    def _run(
        self,
        file_path: str,
        extract_gps: bool = True,
        extract_author: bool = True,
        output_format: str = "json",
        **kwargs: Any
    ) -> str:
        """Execute ExifTool metadata extraction."""
        try:
            safe_log_info(logger, f"[ExifToolTool] Starting", file_path=file_path, extract_gps=extract_gps, extract_author=extract_author, output_format=output_format)
            
            # Validate inputs
            if not file_path or not isinstance(file_path, str):
                error_msg = "file_path must be a non-empty string"
                safe_log_error(logger, error_msg)
                return json.dumps({"status": "error", "message": error_msg})
            
            if output_format not in ["json", "text"]:
                error_msg = "output_format must be 'json' or 'text'"
                safe_log_error(logger, error_msg)
                return json.dumps({"status": "error", "message": error_msg})
            
            # Check Docker availability (Docker-only execution)
            from hackerdogs_tools.osint.docker_client import get_docker_client, execute_in_docker
            import os
            
            docker_client = get_docker_client()
            
            if not docker_client or not docker_client.docker_available:
                error_msg = (
                    "Docker is required for OSINT tools. Setup:\n"
                    "1. Build Docker image: cd hackerdogs_tools/osint/docker && docker build -t osint-tools:latest .\n"
                    "2. Start container: docker-compose up -d"
                )
                safe_log_error(logger, error_msg)
                return json.dumps({"status": "error", "message": error_msg})
            
            # Check if file exists (host-side check)
            if not os.path.exists(file_path):
                error_msg = f"File not found: {file_path}"
                safe_log_error(logger, error_msg)
                return json.dumps({"status": "error", "message": error_msg})
            
            # Build ExifTool command arguments
            args = []
            
            # Output format
            if output_format == "json":
                args.append("-j")  # JSON output
                args.append("-G")  # Include group names (e.g., "EXIF:Make")
            else:
                args.append("-S")  # Short format for text output
            
            # Always include all metadata
            args.append("-a")  # Show all tags (not just EXIF)
            args.append("-u")  # Show unknown tags too
            
            # For docker exec, we need to copy the file into the container
            # since docker exec doesn't support volume mounting
            import subprocess
            
            file_name = os.path.basename(file_path)
            container_file_path = f"/workspace/{file_name}"
            
            # Copy file into container
            try:
                copy_cmd = [
                    "docker", "cp", file_path, f"{docker_client.container_name}:{container_file_path}"
                ]
                copy_result = subprocess.run(
                    copy_cmd,
                    capture_output=True,
                    text=True,
                    timeout=30,
                    check=False
                )
                
                if copy_result.returncode != 0:
                    error_msg = f"Failed to copy file into container: {copy_result.stderr}"
                    safe_log_error(logger, error_msg)
                    return json.dumps({"status": "error", "message": error_msg})
                
                safe_log_info(logger, f"[ExifToolTool] File copied to container", 
                             host_path=file_path, container_path=container_file_path)
            except Exception as e:
                error_msg = f"Failed to copy file into container: {str(e)}"
                safe_log_error(logger, error_msg)
                return json.dumps({"status": "error", "message": error_msg})
            
            args.append(container_file_path)
            
            # Execute ExifTool in Docker (docker exec doesn't support volumes)
            docker_result = execute_in_docker("exiftool", args, timeout=60, volumes=None)
            
            if docker_result["status"] != "success":
                error_msg = f"ExifTool failed: {docker_result.get('stderr', docker_result.get('message', 'Unknown error'))}"
                safe_log_error(logger, error_msg)
                return json.dumps({"status": "error", "message": error_msg})
            
            # Parse output
            stdout = docker_result.get("stdout", "")
            stderr = docker_result.get("stderr", "")
            
            # For JSON output, return verbatim
            if output_format == "json":
                if stdout:
                    # ExifTool JSON output is already valid JSON (array of objects)
                    # Return it verbatim
                    safe_log_info(logger, f"[ExifToolTool] Complete - returning JSON verbatim", file_path=file_path)
                    return stdout
                else:
                    # No metadata found or empty output
                    safe_log_info(logger, f"[ExifToolTool] Complete - no metadata found", file_path=file_path)
                    return json.dumps([])  # Empty array for no results
            
            # For text output, return stdout verbatim
            safe_log_info(logger, f"[ExifToolTool] Complete - returning text verbatim", file_path=file_path)
            return stdout if stdout else stderr
            
        except Exception as e:
            safe_log_error(logger, f"[ExifToolTool] Error: {str(e)}", exc_info=True)
            return json.dumps({"status": "error", "message": f"ExifTool extraction failed: {str(e)}"})
