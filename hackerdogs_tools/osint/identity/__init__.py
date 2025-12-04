"""
Identity & SOCMINT OSINT Tools

This module provides tools for identity hunting including:
- Username enumeration (Sherlock, Maigret)
- Email investigation (GHunt, Holehe)
"""

from .sherlock_langchain import sherlock_search
from .sherlock_crewai import SherlockTool
from .maigret_langchain import maigret_search
from .maigret_crewai import MaigretTool
from .ghunt_langchain import ghunt_query
from .ghunt_crewai import GHuntTool
from .holehe_langchain import holehe_query
from .holehe_crewai import HoleheTool

__all__ = [
    "sherlock_search",
    "SherlockTool",
    "maigret_search",
    "MaigretTool",
    "ghunt_query",
    "GHuntTool",
    "holehe_query",
    "HoleheTool",
]

