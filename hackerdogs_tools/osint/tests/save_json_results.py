"""
Utility to save JSON test results to files.
"""

import json
from pathlib import Path
from datetime import datetime

RESULTS_DIR = Path(__file__).parent / "results"


def save_test_result(tool_name: str, test_type: str, result_data: dict, domain: str = None):
    """
    Save test result JSON to file.
    
    Args:
        tool_name: Name of the tool (e.g., "subfinder", "amass")
        test_type: Type of test ("standalone", "langchain", "crewai")
        result_data: JSON data to save
        domain: Optional domain/test input for filename
    """
    # Ensure results directory exists
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Create filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if domain:
        # Sanitize domain for filename
        safe_domain = domain.replace(".", "_").replace("/", "_")[:50]
        filename = f"{tool_name}_{test_type}_{safe_domain}_{timestamp}.json"
    else:
        filename = f"{tool_name}_{test_type}_{timestamp}.json"
    
    filepath = RESULTS_DIR / filename
    
    # Add metadata
    output = {
        "tool": tool_name,
        "test_type": test_type,
        "timestamp": timestamp,
        "domain": domain,
        "result": result_data
    }
    
    # Write JSON file
    with open(filepath, 'w') as f:
        json.dump(output, f, indent=2)
    
    return filepath

