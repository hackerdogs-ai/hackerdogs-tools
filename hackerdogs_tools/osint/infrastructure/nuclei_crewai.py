"""
Nuclei Tool for CrewAI Agents

Template-based vulnerability scanner using ProjectDiscovery Nuclei.
"""

import json
import subprocess
import shutil
from typing import Any, Optional, List
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error
from hackerdogs_tools.osint.docker_client import get_docker_client, execute_in_docker

logger = setup_logger(__name__, log_file_path="logs/nuclei_tool.log")


class NucleiToolSchema(BaseModel):
    """Input schema for NucleiTool."""
    target: str = Field(..., description="URL or IP to scan")
    templates: Optional[List[str]] = Field(default=None, description="Specific template IDs")
    severity: Optional[str] = Field(default=None, description="Filter by severity (info, low, medium, high, critical)")
    tags: Optional[List[str]] = Field(default=None, description="Filter by tags")


class NucleiTool(BaseTool):
    """Tool for vulnerability scanning using Nuclei."""
    
    name: str = "Nuclei Vulnerability Scanner"
    description: str = (
        "Scan target for vulnerabilities using Nuclei templates. "
        "Detects CVEs, misconfigurations, and security issues."
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
        **kwargs: Any
    ) -> str:
        """Execute Nuclei scan in Docker container."""
        try:
            safe_log_info(logger, f"[NucleiTool] Starting scan", target=target)
            
            args = ["-u", target, "-jsonl", "-o", "-"]
            if templates:
                args.extend(["-t", ",".join(templates)])
            if severity:
                args.extend(["-severity", severity])
            if tags:
                args.extend(["-tags", ",".join(tags)])
            
            # Execute in Docker
            docker_result = execute_in_docker("nuclei", args, timeout=600)
            
            # Exit code 1 can mean findings were found (not an error)
            if docker_result["status"] != "success" and docker_result.get("returncode", -1) not in [0, 1]:
                return json.dumps({
                    "status": "error",
                    "message": docker_result.get("stderr", docker_result.get("message", "Unknown error"))
                })
            
            findings = []
            stdout = docker_result.get("stdout", "")
            for line in stdout.strip().split('\n'):
                if line.strip():
                    try:
                        findings.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
            
            result_data = {
                "status": "success",
                "target": target,
                "findings": findings,
                "count": len(findings),
                "execution_method": "docker"
            }
            
            return json.dumps(result_data, indent=2)
            
        except Exception as e:
            safe_log_error(logger, f"[NucleiTool] Error: {str(e)}", exc_info=True)
            return json.dumps({"status": "error", "message": str(e)})

