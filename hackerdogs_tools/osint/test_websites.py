"""
Test Website Utility Module

Provides random website URL selection from a curated list of working websites
for testing web scraping and crawling tools. This ensures tests use real, valid
URLs instead of placeholder domains like example.com.

Sources:
- Curated list of working websites from different industries (websites.txt)
"""

import os
import random
from typing import List, Optional, Literal
from pathlib import Path


# Path to websites file
_WEBSITES_FILE = Path(__file__).parent / "websites.txt"

# Cache
_WEBSITES_CACHE: Optional[List[str]] = None


def _load_websites() -> List[str]:
    """
    Load website URLs from the websites.txt file.
    
    Returns:
        List of website URLs (one per line, stripped of whitespace)
    
    Raises:
        FileNotFoundError: If the websites file doesn't exist
        IOError: If the file cannot be read
    """
    global _WEBSITES_CACHE
    
    if _WEBSITES_CACHE is not None:
        return _WEBSITES_CACHE
    
    if not _WEBSITES_FILE.exists():
        raise FileNotFoundError(
            f"Websites file not found: {_WEBSITES_FILE}\n"
            f"Please ensure websites.txt exists in hackerdogs_tools/osint/"
        )
    
    try:
        with open(_WEBSITES_FILE, 'r', encoding='utf-8') as f:
            websites = [
                line.strip() 
                for line in f 
                if line.strip() and not line.strip().startswith('#')
            ]
        
        if not websites:
            raise ValueError(f"No valid websites found in {_WEBSITES_FILE}")
        
        _WEBSITES_CACHE = websites
        return websites
    
    except IOError as e:
        raise IOError(f"Failed to read websites file: {e}")


def get_random_website() -> str:
    """
    Get a random website URL from the available website pool.
    
    This is useful for testing web scraping and crawling tools with real, valid
    URLs instead of placeholder domains like example.com.
    
    Returns:
        A random website URL (with protocol)
    
    Example:
        >>> website = get_random_website()
        >>> print(website)
        "https://www.github.com"
    """
    websites = _load_websites()
    return random.choice(websites)


def get_random_websites(
    count: int = 1,
    unique: bool = True
) -> List[str]:
    """
    Get multiple random website URLs from the available website pool.
    
    Args:
        count: Number of websites to return (default: 1)
        unique: If True, ensure all websites are unique (default: True)
    
    Returns:
        List of random website URLs
    
    Raises:
        ValueError: If count exceeds available unique websites
    
    Example:
        >>> websites = get_random_websites(count=5)
        >>> print(websites)
        ["https://www.github.com", "https://www.stackoverflow.com", ...]
    """
    websites = _load_websites()
    
    if unique:
        if count > len(websites):
            raise ValueError(
                f"Requested {count} unique websites, but only {len(websites)} available"
            )
        return random.sample(websites, count)
    else:
        return [random.choice(websites) for _ in range(count)]


def get_website_for_testing() -> str:
    """
    Get a website URL suitable for testing.
    
    This is an alias for get_random_website() for clarity in test code.
    
    Returns:
        A random website URL for testing
    """
    return get_random_website()


def get_test_website() -> str:
    """
    Get a test website URL (alias for get_random_website).
    
    Returns:
        A random website URL for testing
    """
    return get_random_website()


def reset_cache() -> None:
    """
    Reset the website cache.
    
    Useful for testing or if the websites file is updated.
    """
    global _WEBSITES_CACHE
    _WEBSITES_CACHE = None


def get_websites_count() -> int:
    """
    Get the total number of available websites.
    
    Returns:
        Number of websites available
    """
    return len(_load_websites())


# Convenience function for backward compatibility
def random_website() -> str:
    """
    Get a random website URL (alias for get_random_website).
    
    Returns:
        A random website URL
    """
    return get_random_website()


if __name__ == "__main__":
    # Test the module
    print("Testing test_websites module...")
    print("=" * 60)
    print(f"Total websites: {get_websites_count()}")
    print("=" * 60)
    
    print(f"\nRandom website: {get_random_website()}")
    print(f"\n5 random websites: {get_random_websites(5)}")
    print(f"10 random websites (may have duplicates): {get_random_websites(10, unique=False)}")

