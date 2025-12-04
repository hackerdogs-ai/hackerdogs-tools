"""
Test Domain Utility Module

Provides random domain selection from mixed legitimate and malicious domains for testing OSINT tools.
This ensures tests use real, valid domains instead of reserved domains like example.com.

Sources:
- Legitimate domains: opendns-random-domains.txt (~10,000 domains)
- Malicious domains: blackbook.txt + full-domains-*.txt (~160,000 domains)
"""

import os
import random
from typing import List, Optional, Literal
from pathlib import Path


# Paths to domain files
_GOOD_DOMAINS_FILE = Path(__file__).parent / "opendns-random-domains.txt"

# Malicious domain files (in other workspaces)
_MALICIOUS_DOMAINS_FILES = [
    Path("/Users/tejaswiredkar/Documents/GitHub/blackbook/blackbook.txt"),
    Path("/Users/tejaswiredkar/Documents/GitHub/malicious-domains/full-domains-aa.txt"),
    Path("/Users/tejaswiredkar/Documents/GitHub/malicious-domains/full-domains-ab.txt"),
    Path("/Users/tejaswiredkar/Documents/GitHub/malicious-domains/full-domains-ac.txt"),
]

# Caches
_GOOD_DOMAINS_CACHE: Optional[List[str]] = None
_MALICIOUS_DOMAINS_CACHE: Optional[List[str]] = None
_MIXED_DOMAINS_CACHE: Optional[List[str]] = None


def _load_good_domains() -> List[str]:
    """
    Load legitimate domains from the OpenDNS random domains file.
    
    Returns:
        List of legitimate domain names (one per line, stripped of whitespace)
    
    Raises:
        FileNotFoundError: If the domains file doesn't exist
        IOError: If the file cannot be read
    """
    global _GOOD_DOMAINS_CACHE
    
    if _GOOD_DOMAINS_CACHE is not None:
        return _GOOD_DOMAINS_CACHE
    
    if not _GOOD_DOMAINS_FILE.exists():
        raise FileNotFoundError(
            f"Good domains file not found: {_GOOD_DOMAINS_FILE}\n"
            f"Please ensure opendns-random-domains.txt exists in hackerdogs_tools/osint/"
        )
    
    try:
        with open(_GOOD_DOMAINS_FILE, 'r', encoding='utf-8') as f:
            domains = [
                line.strip() 
                for line in f 
                if line.strip() and not line.strip().startswith('#')
            ]
        
        if not domains:
            raise ValueError(f"No valid domains found in {_GOOD_DOMAINS_FILE}")
        
        _GOOD_DOMAINS_CACHE = domains
        return domains
    
    except IOError as e:
        raise IOError(f"Failed to read good domains file: {e}")


def _load_malicious_domains() -> List[str]:
    """
    Load malicious domains from blackbook and malicious-domains files.
    
    Returns:
        List of malicious domain names (deduplicated)
    
    Raises:
        FileNotFoundError: If no malicious domain files are found
        IOError: If files cannot be read
    """
    global _MALICIOUS_DOMAINS_CACHE
    
    if _MALICIOUS_DOMAINS_CACHE is not None:
        return _MALICIOUS_DOMAINS_CACHE
    
    all_malicious = set()
    found_files = []
    
    for file_path in _MALICIOUS_DOMAINS_FILES:
        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    domains = [
                        line.strip() 
                        for line in f 
                        if line.strip() and not line.strip().startswith('#')
                    ]
                    all_malicious.update(domains)
                    found_files.append(file_path.name)
            except IOError as e:
                # Log but continue with other files
                print(f"Warning: Could not read {file_path}: {e}")
        else:
            # Try relative path from hackerdogs-tools
            alt_path = Path(__file__).parent.parent.parent.parent / file_path.name
            if alt_path.exists():
                try:
                    with open(alt_path, 'r', encoding='utf-8') as f:
                        domains = [
                            line.strip() 
                            for line in f 
                            if line.strip() and not line.strip().startswith('#')
                        ]
                        all_malicious.update(domains)
                        found_files.append(file_path.name)
                except IOError as e:
                    print(f"Warning: Could not read {alt_path}: {e}")
    
    if not all_malicious:
        raise FileNotFoundError(
            f"No malicious domain files found. Expected files:\n"
            f"  - {_MALICIOUS_DOMAINS_FILES[0]}\n"
            f"  - {_MALICIOUS_DOMAINS_FILES[1]}\n"
            f"  - {_MALICIOUS_DOMAINS_FILES[2]}\n"
            f"  - {_MALICIOUS_DOMAINS_FILES[3]}"
        )
    
    _MALICIOUS_DOMAINS_CACHE = list(all_malicious)
    print(f"Loaded {len(_MALICIOUS_DOMAINS_CACHE)} malicious domains from {len(found_files)} files")
    return _MALICIOUS_DOMAINS_CACHE


def _load_mixed_domains() -> List[str]:
    """
    Load and mix legitimate and malicious domains.
    
    Returns:
        Combined list of all domains (good + malicious)
    """
    global _MIXED_DOMAINS_CACHE
    
    if _MIXED_DOMAINS_CACHE is not None:
        return _MIXED_DOMAINS_CACHE
    
    good = _load_good_domains()
    malicious = _load_malicious_domains()
    
    # Mix them together
    _MIXED_DOMAINS_CACHE = good + malicious
    return _MIXED_DOMAINS_CACHE


def get_random_domain(
    domain_type: Literal["good", "malicious", "mixed"] = "mixed"
) -> str:
    """
    Get a random domain from the available domain pools.
    
    This is useful for testing OSINT tools with real, valid domains
    instead of reserved domains like example.com. By default, returns
    a mixed domain (both legitimate and malicious) to test tools
    against various scenarios.
    
    Args:
        domain_type: Type of domain to return
            - "good": Only legitimate domains from OpenDNS
            - "malicious": Only malicious domains from blackbook/malicious-domains
            - "mixed": Mixed pool of both (default)
    
    Returns:
        A random domain name
    
    Example:
        >>> domain = get_random_domain()
        >>> print(domain)
        "example.org"
        
        >>> malicious = get_random_domain("malicious")
        >>> print(malicious)
        "statsrvv.com"
    """
    if domain_type == "good":
        domains = _load_good_domains()
    elif domain_type == "malicious":
        domains = _load_malicious_domains()
    else:  # mixed
        domains = _load_mixed_domains()
    
    return random.choice(domains)


def get_random_domains(count: int = 1, unique: bool = True) -> List[str]:
    """
    Get multiple random domains from the OpenDNS random domains list.
    
    Args:
        count: Number of domains to return (default: 1)
        unique: If True, ensure all domains are unique (default: True)
    
    Returns:
        List of random domain names
    
    Raises:
        ValueError: If count exceeds available unique domains
    
    Example:
        >>> domains = get_random_domains(count=5)
        >>> print(domains)
        ["example.org", "test.net", "sample.com", "demo.io", "site.org"]
    """
    domains = _load_domains()
    
    if unique:
        if count > len(domains):
            raise ValueError(
                f"Requested {count} unique domains, but only {len(domains)} available"
            )
        return random.sample(domains, count)
    else:
        return [random.choice(domains) for _ in range(count)]


def get_domain_for_testing() -> str:
    """
    Get a domain suitable for testing.
    
    This is an alias for get_random_domain() for clarity in test code.
    
    Returns:
        A random domain name for testing
    """
    return get_random_domain()


def get_test_domain() -> str:
    """
    Get a test domain (alias for get_random_domain).
    
    Returns:
        A random domain name for testing
    """
    return get_random_domain()


def reset_cache() -> None:
    """
    Reset the domains cache.
    
    Useful for testing or if the domains file is updated.
    """
    global _DOMAINS_CACHE
    _DOMAINS_CACHE = None


def get_domains_count() -> int:
    """
    Get the total number of available domains.
    
    Returns:
        Number of domains in the file
    """
    return len(_load_domains())


# Convenience function for backward compatibility
def random_domain() -> str:
    """
    Get a random domain (alias for get_random_domain).
    
    Returns:
        A random domain name
    """
    return get_random_domain()


if __name__ == "__main__":
    # Test the module
    print("Testing test_domains module...")
    print(f"Total domains available: {get_domains_count()}")
    print(f"\nRandom domain: {get_random_domain()}")
    print(f"\n5 random domains: {get_random_domains(5)}")
    print(f"\n10 unique domains: {get_random_domains(10, unique=True)}")

