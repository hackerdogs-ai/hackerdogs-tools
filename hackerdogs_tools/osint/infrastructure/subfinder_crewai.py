"""
Subfinder Tool for CrewAI Agents

Fast passive subdomain discovery using ProjectDiscovery Subfinder.
"""

import json
import subprocess
import shutil
from typing import Any, Optional
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error
from hackerdogs_tools.osint.docker_client import get_docker_client, execute_in_docker

logger = setup_logger(__name__, log_file_path="logs/subfinder_tool.log")


class SubfinderToolSchema(BaseModel):
    """Input schema for SubfinderTool."""
    domain: str = Field(..., description="Target domain to enumerate")
    recursive: bool = Field(default=False, description="Recursive enumeration")
    silent: bool = Field(default=True, description="Silent mode")
    sources: Optional[str] = Field(default=None, description="Comma-separated list of specific sources (e.g., 'crtsh,github')")
    exclude_sources: Optional[str] = Field(default=None, description="Comma-separated list of sources to exclude")
    all_sources: bool = Field(default=False, description="Use all sources for enumeration (slow)")
    rate_limit: Optional[int] = Field(default=None, description="Maximum HTTP requests per second")
    timeout: int = Field(default=30, description="Seconds to wait before timing out")
    max_time: int = Field(default=10, description="Minutes to wait for enumeration results")
    provider_config: Optional[str] = Field(default=None, description="Path to custom provider config file")
    config: Optional[str] = Field(default=None, description="Path to custom flag config file")
    active: bool = Field(default=False, description="Display active subdomains only")
    include_ip: bool = Field(default=False, description="Include host IP in output (active only)")
    collect_sources: bool = Field(default=False, description="Include all sources in output (JSON only)")


class SubfinderTool(BaseTool):
    """Tool for fast passive subdomain discovery using Subfinder."""
    
    name: str = "Subfinder Subdomain Discovery"
    description: str = (
        "Fast passive subdomain discovery using Subfinder. "
        "Use this for quick subdomain enumeration from passive sources."
    )
    args_schema: type[BaseModel] = SubfinderToolSchema
    
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
        domain: str,
        recursive: bool = False,
        silent: bool = True,
        sources: Optional[str] = None,
        exclude_sources: Optional[str] = None,
        all_sources: bool = False,
        rate_limit: Optional[int] = None,
        timeout: int = 30,
        max_time: int = 10,
        provider_config: Optional[str] = None,
        config: Optional[str] = None,
        active: bool = False,
        include_ip: bool = False,
        collect_sources: bool = False,
        **kwargs: Any
    ) -> str:
        """Execute Subfinder enumeration in Docker container."""
        try:
            safe_log_info(logger, f"[SubfinderTool] Starting", domain=domain)
            
            # Build command arguments
            args = ["-d", domain, "-oJ", "-"]
            
            # Source options
            if all_sources:
                args.append("-all")
            elif sources:
                args.extend(["-s"] + sources.split(","))
            
            if exclude_sources:
                args.extend(["-es"] + exclude_sources.split(","))
            
            if recursive:
                args.append("-recursive")
            
            # Rate limiting
            if rate_limit:
                args.extend(["-rl", str(rate_limit)])
            
            # Timeouts
            if timeout:
                args.extend(["-timeout", str(timeout)])
            if max_time:
                args.extend(["-max-time", str(max_time)])
            
            # Config files
            if provider_config:
                args.extend(["-pc", provider_config])
            if config:
                args.extend(["-config", config])
            
            # Output options
            if active:
                args.append("-nW")
            if include_ip:
                args.append("-oI")
            if collect_sources:
                args.append("-cs")
            if silent:
                args.append("-silent")
            
            # Execute in Docker
            # Note: Config files must be mounted into container or use default locations
            docker_result = execute_in_docker("subfinder", args, timeout=(max_time * 60) + 60)
            
            if docker_result["status"] != "success":
                return json.dumps({
                    "status": "error",
                    "message": docker_result.get("stderr", docker_result.get("message", "Unknown error"))
                })
            
            stdout = docker_result.get("stdout", "")
            stderr = docker_result.get("stderr", "")
            
            # Return raw output verbatim - no parsing, no reformatting
            return stdout if stdout else stderr
            
        except Exception as e:
            safe_log_error(logger, f"[SubfinderTool] Error: {str(e)}", exc_info=True)
            return json.dumps({"status": "error", "message": str(e)})

