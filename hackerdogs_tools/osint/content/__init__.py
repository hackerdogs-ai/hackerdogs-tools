"""
Content & Dark Web OSINT Tools

This module provides tools for content gathering including:
- Web scraping (Scrapy)
- Historical URL discovery (Waybackurls)
- Dark web search (OnionSearch)
"""

from .scrapy_langchain import scrapy_search
from .scrapy_crewai import ScrapyTool
from .waybackurls_langchain import waybackurls_search
from .waybackurls_crewai import WaybackurlsTool
from .onionsearch_langchain import onionsearch_search
from .onionsearch_crewai import OnionSearchTool

__all__ = [
    "scrapy_search",
    "ScrapyTool",
    "waybackurls_search",
    "WaybackurlsTool",
    "onionsearch_search",
    "OnionSearchTool",
]

