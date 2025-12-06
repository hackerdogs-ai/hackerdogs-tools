"""
Nuclei Tool for CrewAI Agents

Template-based vulnerability scanner using ProjectDiscovery Nuclei.
"""

import json
import subprocess
from typing import Any, Optional, List
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error
from hackerdogs_tools.osint.docker_client import get_docker_client, execute_in_docker

logger = setup_logger(__name__, log_file_path="logs/nuclei_tool.log")


class NucleiToolSchema(BaseModel):
    """Input schema for NucleiTool."""
    target: str = Field(..., description="URL or IP to scan (e.g., 'https://example.com' or '192.168.1.1')")
    templates: Optional[List[str]] = Field(default=None, description="Specific template IDs to use (default: all templates)")
    severity: Optional[str] = Field(default=None, description="Filter by severity: 'info', 'low', 'medium', 'high', 'critical'. Can specify multiple: 'critical,high'")
    tags: Optional[List[str]] = Field(default=None, description="Filter by template tags (e.g., ['cve', 'xss', 'sqli'])")
    rate_limit: Optional[int] = Field(default=None, ge=1, le=1000, description="Maximum requests per second (recommended: 50-150)")
    concurrency: Optional[int] = Field(default=None, ge=1, le=200, description="Number of concurrent requests (recommended: 25-50)")


class NucleiTool(BaseTool):
    """Tool for vulnerability scanning using Nuclei."""
    
    name: str = "Nuclei Vulnerability Scanner"
    description: str = (
        "Scan target for vulnerabilities using Nuclei templates. "
        "Detects CVEs, misconfigurations, and security issues. "
        "Best practices: Use rate limiting to avoid overwhelming targets, "
        "filter by severity to focus on critical issues, and use specific templates for targeted scanning."
    )
    args_schema: type[BaseModel] = NucleiToolSchema
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        # Docker-only - no host binaries allowed
        docker_client = get_docker_client()
        if not docker_client or not docker_client.docker_available:
            raise ValueError(
                "Docker is required for OSINT tools. Setup:\n"
                "1. Build Docker image: cd hackerdogs_tools/osint/docker && docker build -t osint-tools:latest .\n"
                "2. Start container: docker-compose up -d"
            )
    
    def _run(
        self,
        target: str,
        templates: Optional[List[str]] = None,
        severity: Optional[str] = None,
        tags: Optional[List[str]] = None,
        rate_limit: Optional[int] = None,
        concurrency: Optional[int] = None,
        **kwargs: Any
    ) -> str:
        """
        Execute Nuclei scan in Docker container.
        
        Reference: https://docs.projectdiscovery.io/opensource/nuclei/usage
        """
        try:
            safe_log_info(logger, f"[NucleiTool] Starting scan", target=target)
            
            # Build Nuclei command arguments
            args = ["-u", target, "-jsonl", "-o", "-"]
            
            # Template selection
            if templates:
                args.extend(["-t", ",".join(templates)])
            
            # Severity filtering (e.g., "critical,high" or "critical")
            if severity:
                args.extend(["-severity", severity])
            
            # Tag filtering
            if tags:
                args.extend(["-tags", ",".join(tags)])
            
            # Rate limiting (requests per second)
            if rate_limit:
                args.extend(["-rate-limit", str(rate_limit)])
            
            # Concurrency control
            if concurrency:
                args.extend(["-c", str(concurrency)])
            
            # Execute in Docker (uses official projectdiscovery/nuclei image if available)
            docker_result = execute_in_docker("nuclei", args, timeout=600)
            
            # Nuclei exit codes:
            # 0 = Success, no findings
            # 1 = Success, findings found (not an error)
            # >1 = Actual error
            returncode = docker_result.get("returncode", -1)
            if docker_result["status"] != "success" and returncode not in [0, 1]:
                error_msg = docker_result.get("stderr", docker_result.get("message", "Unknown error"))
                safe_log_error(logger, f"[NucleiTool] Docker execution failed", 
                             error=error_msg, returncode=returncode)
                return json.dumps({
                    "status": "error",
                    "message": f"Nuclei scan failed: {error_msg}",
                    "returncode": returncode
                })
            
            stdout = docker_result.get("stdout", "")
            stderr = docker_result.get("stderr", "")
            
            # Return raw output verbatim - no parsing, no reformatting
            return stdout if stdout else stderr
            
        except subprocess.TimeoutExpired:
            error_msg = "Nuclei scan timed out after 600 seconds"
            safe_log_error(logger, f"[NucleiTool] {error_msg}", target=target)
            return json.dumps({"status": "error", "message": error_msg})
        except Exception as e:
            safe_log_error(logger, f"[NucleiTool] Unexpected error: {str(e)}", target=target, exc_info=True)
            return json.dumps({"status": "error", "message": f"Unexpected error: {str(e)}"})

