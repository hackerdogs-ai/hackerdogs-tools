"""
Test Identity Data Utility Module

Provides random username and email selection from usernames.txt for testing identity OSINT tools.
This ensures tests use real, valid usernames and emails instead of placeholder values.

Sources:
- Emails: usernames.txt (contains emails, usernames extracted from before @)
- Usernames: Extracted from emails (substring before @)
"""

import os
import random
from typing import List, Optional
from pathlib import Path


# Path to usernames file
_USERNAMES_FILE = Path(__file__).parent / "tests" / "usernames.txt"

# Caches
_EMAILS_CACHE: Optional[List[str]] = None
_USERNAMES_CACHE: Optional[List[str]] = None


def _load_emails() -> List[str]:
    """
    Load emails from the usernames.txt file.
    
    Returns:
        List of email addresses (one per line, stripped of whitespace)
    
    Raises:
        FileNotFoundError: If the usernames file doesn't exist
        IOError: If the file cannot be read
    """
    global _EMAILS_CACHE
    
    if _EMAILS_CACHE is not None:
        return _EMAILS_CACHE
    
    if not _USERNAMES_FILE.exists():
        raise FileNotFoundError(
            f"Usernames file not found: {_USERNAMES_FILE}\n"
            f"Please ensure usernames.txt exists in hackerdogs_tools/osint/tests/"
        )
    
    try:
        with open(_USERNAMES_FILE, 'r', encoding='utf-8') as f:
            emails = [
                line.strip() 
                for line in f 
                if line.strip() and not line.strip().startswith('#') and '@' in line.strip()
            ]
        
        if not emails:
            raise ValueError(f"No valid emails found in {_USERNAMES_FILE}")
        
        _EMAILS_CACHE = emails
        return emails
    
    except IOError as e:
        raise IOError(f"Failed to read usernames file: {e}")


def _load_usernames() -> List[str]:
    """
    Extract usernames from emails (substring before @).
    
    Returns:
        List of unique usernames extracted from emails
    """
    global _USERNAMES_CACHE
    
    if _USERNAMES_CACHE is not None:
        return _USERNAMES_CACHE
    
    emails = _load_emails()
    usernames = set()
    
    for email in emails:
        if '@' in email:
            username = email.split('@')[0].strip()
            if username:  # Only add non-empty usernames
                usernames.add(username)
    
    if not usernames:
        raise ValueError(f"No valid usernames could be extracted from {_USERNAMES_FILE}")
    
    _USERNAMES_CACHE = list(usernames)
    return _USERNAMES_CACHE


def get_random_username() -> str:
    """
    Get a random username extracted from emails.
    
    Usernames are extracted as the substring before @ in email addresses.
    This is useful for testing username enumeration tools like Sherlock and Maigret.
    
    Returns:
        A random username (extracted from email addresses)
    
    Example:
        >>> username = get_random_username()
        >>> print(username)
        "asmith"
    """
    usernames = _load_usernames()
    return random.choice(usernames)


def get_random_usernames(
    count: int = 1,
    unique: bool = True
) -> List[str]:
    """
    Get multiple random usernames.
    
    Args:
        count: Number of usernames to return (default: 1)
        unique: If True, ensure all usernames are unique (default: True)
    
    Returns:
        List of random usernames
    
    Raises:
        ValueError: If count exceeds available unique usernames
    
    Example:
        >>> usernames = get_random_usernames(count=5)
        >>> print(usernames)
        ["asmith", "bjohnson", "cwilliams", "djones", "ebrown"]
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


def get_random_email() -> str:
    """
    Get a random email address from the usernames.txt file.
    
    This is useful for testing email investigation tools like GHunt and Holehe.
    
    Returns:
        A random email address
    
    Example:
        >>> email = get_random_email()
        >>> print(email)
        "asmith@gmail.com"
    """
    emails = _load_emails()
    return random.choice(emails)


def get_random_emails(
    count: int = 1,
    unique: bool = True
) -> List[str]:
    """
    Get multiple random email addresses.
    
    Args:
        count: Number of emails to return (default: 1)
        unique: If True, ensure all emails are unique (default: True)
    
    Returns:
        List of random email addresses
    
    Raises:
        ValueError: If count exceeds available unique emails
    
    Example:
        >>> emails = get_random_emails(count=3)
        >>> print(emails)
        ["asmith@gmail.com", "bjohnson@hotmail.com", "cwilliams@gmail.com"]
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


def get_username_from_email(email: str) -> str:
    """
    Extract username from an email address.
    
    Args:
        email: Email address (e.g., "asmith@gmail.com")
    
    Returns:
        Username extracted from email (e.g., "asmith")
    
    Raises:
        ValueError: If email doesn't contain @
    
    Example:
        >>> username = get_username_from_email("asmith@gmail.com")
        >>> print(username)
        "asmith"
    """
    if '@' not in email:
        raise ValueError(f"Invalid email address: {email}")
    
    return email.split('@')[0].strip()


def reset_cache() -> None:
    """
    Reset all identity data caches.
    
    Useful for testing or if the usernames file is updated.
    """
    global _EMAILS_CACHE, _USERNAMES_CACHE
    _EMAILS_CACHE = None
    _USERNAMES_CACHE = None


def get_emails_count() -> int:
    """
    Get the total number of available email addresses.
    
    Returns:
        Number of emails available
    """
    return len(_load_emails())


def get_usernames_count() -> int:
    """
    Get the total number of available unique usernames.
    
    Returns:
        Number of unique usernames available
    """
    return len(_load_usernames())


if __name__ == "__main__":
    # Test the module
    print("Testing test_identity_data module...")
    print("=" * 60)
    print(f"Total emails: {get_emails_count():,}")
    print(f"Unique usernames: {get_usernames_count():,}")
    print("=" * 60)
    
    print(f"\nRandom username: {get_random_username()}")
    print(f"Random email: {get_random_email()}")
    
    print(f"\n5 random usernames: {get_random_usernames(5)}")
    print(f"5 random emails: {get_random_emails(5)}")
    
    # Test username extraction
    test_email = get_random_email()
    print(f"\nExtract username from '{test_email}': {get_username_from_email(test_email)}")
