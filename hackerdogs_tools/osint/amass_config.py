"""
Amass Configuration and Data Directory Management

This module provides utilities for managing Amass database storage locations
following project structure conventions.
"""

import os
from pathlib import Path


def get_amass_data_dir() -> str:
    """
    Get the Amass data directory path.
    
    Priority:
    1. AMASS_DATA_DIR environment variable (if set)
    2. Project-relative path: hackerdogs_tools/osint/data/amass/
    3. Fallback to ~/.config/amass (for compatibility)
    
    Returns:
        Absolute path to Amass data directory
    """
    # Check environment variable first
    env_dir = os.getenv("AMASS_DATA_DIR")
    if env_dir:
        data_dir = Path(env_dir).expanduser().resolve()
        data_dir.mkdir(parents=True, exist_ok=True)
        return str(data_dir)
    
    # Use project-relative path
    # Get the osint module directory
    osint_module_dir = Path(__file__).parent.resolve()
    
    # Create data/amass subdirectory
    data_dir = osint_module_dir / "data" / "amass"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    return str(data_dir)


def get_amass_results_dir() -> str:
    """
    Get the Amass results/output directory path.
    
    This is where Amass visualization files and other outputs are stored.
    
    Priority:
    1. AMASS_RESULTS_DIR environment variable (if set)
    2. Project-relative path: hackerdogs_tools/osint/tests/results/amass/
    3. Fallback to data/amass/results/
    
    Returns:
        Absolute path to Amass results directory
    """
    # Check environment variable first
    env_dir = os.getenv("AMASS_RESULTS_DIR")
    if env_dir:
        results_dir = Path(env_dir).expanduser().resolve()
        results_dir.mkdir(parents=True, exist_ok=True)
        return str(results_dir)
    
    # Use project-relative path in tests/results/amass
    osint_module_dir = Path(__file__).parent.resolve()
    results_dir = osint_module_dir / "tests" / "results" / "amass"
    results_dir.mkdir(parents=True, exist_ok=True)
    
    return str(results_dir)

