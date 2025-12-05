"""
Utility to save JSON test results to files.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Any

RESULTS_DIR = Path(__file__).parent / "results"


class CustomJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle non-serializable objects."""
    def default(self, obj):
        # Try to convert to dict if it has __dict__
        if hasattr(obj, '__dict__'):
            return obj.__dict__
        # Try to convert to string representation
        try:
            return str(obj)
        except Exception:
            return repr(obj)


def serialize_object(obj: Any) -> Any:
    """
    Recursively serialize an object to JSON-serializable format.
    
    Handles:
    - LangChain message objects
    - CrewAI result objects
    - Custom objects with __dict__
    - Lists and dicts
    """
    if isinstance(obj, dict):
        return {k: serialize_object(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [serialize_object(item) for item in obj]
    elif hasattr(obj, '__dict__'):
        # Try to get dict representation
        try:
            obj_dict = {}
            for key, value in obj.__dict__.items():
                # Skip private attributes
                if not key.startswith('_'):
                    obj_dict[key] = serialize_object(value)
            return obj_dict
        except Exception:
            return str(obj)
    elif hasattr(obj, 'model_dump'):
        # Pydantic models
        try:
            return serialize_object(obj.model_dump())
        except Exception:
            return str(obj)
    elif hasattr(obj, 'dict'):
        # Pydantic v1 models
        try:
            return serialize_object(obj.dict())
        except Exception:
            return str(obj)
    else:
        # Try to convert to string if not JSON serializable
        try:
            json.dumps(obj)
            return obj
        except (TypeError, ValueError):
            return str(obj)


def save_test_result(tool_name: str, test_type: str, result_data: dict, domain: str = None):
    """
    Save test result JSON to file.
    
    Saves verbatim tool responses WITHOUT any wrappers (no tool:, test_type:, etc.).
    Only saves the actual tool response data.
    
    Args:
        tool_name: Name of the tool (e.g., "subfinder", "amass") - used only for filename
        test_type: Type of test ("standalone", "langchain", "crewai") - used only for filename
        result_data: JSON data to save (can contain complex objects) - saved VERBATIM
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
    
    # Serialize complex objects in result_data
    serialized_result = serialize_object(result_data)
    
    # Save VERBATIM - no wrappers, just the result data directly
    # Write JSON file with custom encoder
    with open(filepath, 'w') as f:
        json.dump(serialized_result, f, indent=2, cls=CustomJSONEncoder, ensure_ascii=False)
    
    return filepath

