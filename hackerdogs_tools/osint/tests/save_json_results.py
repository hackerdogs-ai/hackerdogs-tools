"""
Utility to save JSON test results to files.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Any

RESULTS_DIR = Path(__file__).parent / "results"


def serialize_crewai_result(result: Any) -> dict:
    """
    Serialize CrewAI result object to dictionary.
    
    CrewAI result is a CrewOutput (Pydantic BaseModel) which can be serialized
    using model_dump() or dict() methods.
    
    Args:
        result: CrewAI result object from crew.kickoff()
        
    Returns:
        Dictionary representation of the complete CrewAI result
    """
    try:
        # Try Pydantic v2 method first
        if hasattr(result, 'model_dump'):
            return result.model_dump(mode='json')
        # Fallback to Pydantic v1 method
        elif hasattr(result, 'dict'):
            return result.dict()
        # Fallback to dict() if it's already a dict-like object
        elif hasattr(result, '__dict__'):
            return result.__dict__
        # Last resort: convert to string and try to parse
        else:
            return {"raw": str(result)}
    except Exception as e:
        # If serialization fails, return error info
        return {
            "serialization_error": str(e),
            "result_type": str(type(result)),
            "raw": str(result)
        }


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
    # Use default=str to handle non-serializable objects (like Pydantic models, etc.)
    with open(filepath, 'w') as f:
        json.dump(output, f, indent=2, default=str, ensure_ascii=False)  # ensure_ascii=False preserves unicode
    
    return filepath

