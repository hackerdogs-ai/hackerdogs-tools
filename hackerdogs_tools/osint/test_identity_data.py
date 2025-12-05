"""
Test Identity Data Utility Module

Provides random username and email selection for testing identity OSINT tools.
This ensures tests use realistic, valid usernames and emails instead of hardcoded test values.

Sources:
- Usernames: test-usernames.txt (realistic usernames from various sources)
- Emails: test-emails.txt (realistic email addresses)
"""

import os
import random
from typing import List, Optional, Literal
from pathlib import Path


# Paths to data files
_USERNAMES_FILE = Path(__file__).parent / "test-usernames.txt"
_EMAILS_FILE = Path(__file__).parent / "test-emails.txt"

# Caches
_USERNAMES_CACHE: Optional[List[str]] = None
_EMAILS_CACHE: Optional[List[str]] = None


def _load_usernames() -> List[str]:
    """
    Load usernames from the test usernames file.
    
    Returns:
        List of usernames (one per line, stripped of whitespace)
    
    Raises:
        FileNotFoundError: If the usernames file doesn't exist
        IOError: If the file cannot be read
    """
    global _USERNAMES_CACHE
    
    if _USERNAMES_CACHE is not None:
        return _USERNAMES_CACHE
    
    if not _USERNAMES_FILE.exists():
        raise FileNotFoundError(
            f"Usernames file not found: {_USERNAMES_FILE}\n"
            f"Please ensure test-usernames.txt exists in hackerdogs_tools/osint/"
        )
    
    try:
        with open(_USERNAMES_FILE, 'r', encoding='utf-8') as f:
            usernames = [
                line.strip() 
                for line in f 
                if line.strip() and not line.strip().startswith('#')
            ]
        
        if not usernames:
            raise ValueError(f"No valid usernames found in {_USERNAMES_FILE}")
        
        _USERNAMES_CACHE = usernames
        return usernames
    
    except IOError as e:
        raise IOError(f"Failed to read usernames file: {e}")


def _load_emails() -> List[str]:
    """
    Load emails from the test emails file.
    
    Returns:
        List of email addresses (one per line, stripped of whitespace)
    
    Raises:
        FileNotFoundError: If the emails file doesn't exist
        IOError: If the file cannot be read
    """
    global _EMAILS_CACHE
    
    if _EMAILS_CACHE is not None:
        return _EMAILS_CACHE
    
    if not _EMAILS_FILE.exists():
        raise FileNotFoundError(
            f"Emails file not found: {_EMAILS_FILE}\n"
            f"Please ensure test-emails.txt exists in hackerdogs_tools/osint/"
        )
    
    try:
        with open(_EMAILS_FILE, 'r', encoding='utf-8') as f:
            emails = [
                line.strip() 
                for line in f 
                if line.strip() and not line.strip().startswith('#')
            ]
        
        if not emails:
            raise ValueError(f"No valid emails found in {_EMAILS_FILE}")
        
        _EMAILS_CACHE = emails
        return emails
    
    except IOError as e:
        raise IOError(f"Failed to read emails file: {e}")


def get_random_username() -> str:
    """
    Get a random username from the available username pool.
    
    This is useful for testing identity OSINT tools (sherlock, maigret) with
    realistic usernames instead of hardcoded test values.
    
    Returns:
        A random username
    
    Example:
        >>> username = get_random_username()
        >>> print(username)
        "johndoe"
    """
    usernames = _load_usernames()
    return random.choice(usernames)


def get_random_email() -> str:
    """
    Get a random email from the available email pool.
    
    This is useful for testing identity OSINT tools (ghunt, holehe) with
    realistic email addresses instead of hardcoded test values.
    
    Returns:
        A random email address
    
    Example:
        >>> email = get_random_email()
        >>> print(email)
        "john.doe@example.com"
    """
    emails = _load_emails()
    return random.choice(emails)


def get_random_usernames(count: int = 1, unique: bool = True) -> List[str]:
    """
    Get multiple random usernames.
    
    Args:
        count: Number of usernames to return (default: 1)
        unique: If True, ensure all usernames are unique (default: True)
    
    Returns:
        List of random usernames
    
    Raises:
        ValueError: If count exceeds available unique usernames
    """
    usernames = _load_usernames()
    
    if unique:
        if count > len(usernames):
            raise ValueError(
                f"Requested {count} unique usernames, but only {len(usernames)} available"
            )
        return random.sample(usernames, count)
    else:
        return [random.choice(usernames) for _ in range(count)]


def get_random_emails(count: int = 1, unique: bool = True) -> List[str]:
    """
    Get multiple random emails.
    
    Args:
        count: Number of emails to return (default: 1)
        unique: If True, ensure all emails are unique (default: True)
    
    Returns:
        List of random email addresses
    
    Raises:
        ValueError: If count exceeds available unique emails
    """
    emails = _load_emails()
    
    if unique:
        if count > len(emails):
            raise ValueError(
                f"Requested {count} unique emails, but only {len(emails)} available"
            )
        return random.sample(emails, count)
    else:
        return [random.choice(emails) for _ in range(count)]


def reset_cache() -> None:
    """
    Reset all data caches.
    
    Useful for testing or if the data files are updated.
    """
    global _USERNAMES_CACHE, _EMAILS_CACHE
    _USERNAMES_CACHE = None
    _EMAILS_CACHE = None


def get_usernames_count() -> int:
    """
    Get the total number of available usernames.
    
    Returns:
        Number of usernames available
    """
    return len(_load_usernames())


def get_emails_count() -> int:
    """
    Get the total number of available emails.
    
    Returns:
        Number of emails available
    """
    return len(_load_emails())


if __name__ == "__main__":
    # Test the module
    print("Testing test_identity_data module...")
    print("=" * 60)
    print(f"Usernames: {get_usernames_count():,}")
    print(f"Emails: {get_emails_count():,}")
    print("=" * 60)
    
    print(f"\nRandom username: {get_random_username()}")
    print(f"Random email: {get_random_email()}")
    
    print(f"\n5 random usernames: {get_random_usernames(5)}")
    print(f"5 random emails: {get_random_emails(5)}")

