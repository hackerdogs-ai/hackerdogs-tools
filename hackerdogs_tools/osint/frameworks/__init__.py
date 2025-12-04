"""
OSINT Framework Tools

This module provides comprehensive OSINT framework tools:
- SpiderFoot (all-in-one OSINT framework)
"""

from .spiderfoot_langchain import spiderfoot_search
from .spiderfoot_crewai import SpiderFootTool

__all__ = [
    "spiderfoot_search",
    "SpiderFootTool",
]

