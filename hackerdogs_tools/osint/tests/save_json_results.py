"""
Utility to save JSON test results to files.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List

RESULTS_DIR = Path(__file__).parent / "results"


def serialize_langchain_message(message: Any) -> Dict[str, Any]:
    """
    Serialize a LangChain message object to a dictionary.

    Args:
        message: LangChain message object (HumanMessage, AIMessage, ToolMessage, etc.)

    Returns:
        Dictionary representation of the message
    """
    try:
        if hasattr(message, 'model_dump'):
            return message.model_dump(mode='json')
        elif hasattr(message, 'dict'):
            return message.dict()
        elif hasattr(message, '__dict__'):
            msg_dict = {}
            # Extract common attributes
            if hasattr(message, 'content'):
                msg_dict['content'] = message.content
            if hasattr(message, 'additional_kwargs'):
                msg_dict['additional_kwargs'] = message.additional_kwargs
            if hasattr(message, 'response_metadata'):
                msg_dict['response_metadata'] = message.response_metadata
            if hasattr(message, 'id'):
                msg_dict['id'] = message.id
            if hasattr(message, 'name'):
                msg_dict['name'] = message.name
            if hasattr(message, 'tool_call_id'):
                msg_dict['tool_call_id'] = message.tool_call_id
            if hasattr(message, 'tool_calls'):
                msg_dict['tool_calls'] = message.tool_calls
            msg_dict['type'] = message.__class__.__name__
            return msg_dict
        else:
            return {"raw": str(message), "type": type(message).__name__}
    except Exception as e:
        return {
            "serialization_error": str(e),
            "message_type": str(type(message)),
            "raw": str(message)
        }


def serialize_langchain_result(result: Any) -> Dict[str, Any]:
    """
    Serialize LangChain agent result to a dictionary.

    Args:
        result: LangChain agent result (dict with 'messages' key)

    Returns:
        Dictionary with properly serialized messages
    """
    if not isinstance(result, dict):
        if hasattr(result, 'model_dump'):
            result = result.model_dump(mode='json')
        elif hasattr(result, 'dict'):
            result = result.dict()
        elif hasattr(result, '__dict__'):
            result = result.__dict__
        else:
            return {"raw": str(result), "type": type(result).__name__}

    serialized = result.copy()
    if "messages" in serialized and isinstance(serialized["messages"], list):
        serialized["messages"] = [
            serialize_langchain_message(msg) for msg in serialized["messages"]
        ]
    return serialized


def serialize_crewai_result(result: Any) -> dict:
    """
    Serialize CrewAI result object to dictionary.

    Args:
        result: CrewAI result object from crew.kickoff()

    Returns:
        Dictionary representation of the complete CrewAI result
    """
    try:
        if hasattr(result, 'model_dump'):
            return result.model_dump(mode='json')
        elif hasattr(result, 'dict'):
            return result.dict()
        elif hasattr(result, '__dict__'):
            return result.__dict__
        else:
            return {"raw": str(result)}
    except Exception as e:
        return {
            "serialization_error": str(e),
            "result_type": str(type(result)),
            "raw": str(result)
        }


class CustomJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle non-serializable objects."""
    def default(self, obj):
        if hasattr(obj, '__dict__'):
            return obj.__dict__
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
        try:
            obj_dict = {}
            for key, value in obj.__dict__.items():
                if not key.startswith('_'):
                    obj_dict[key] = serialize_object(value)
            return obj_dict
        except Exception:
            return str(obj)
    elif hasattr(obj, 'model_dump'):
        try:
            return serialize_object(obj.model_dump())
        except Exception:
            return str(obj)
    elif hasattr(obj, 'dict'):
        try:
            return serialize_object(obj.dict())
        except Exception:
            return str(obj)
    else:
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
    
    # Serialize result_data properly according to test type
    if test_type == "langchain" and "result" in result_data:
        # Special serialization for LangChain tests
        serialized_result_data = result_data.copy()
        result_value = serialized_result_data["result"]
        if isinstance(result_value, dict):
            serialized_result_data["result"] = serialize_langchain_result(result_value)
        elif hasattr(result_value, 'model_dump'):
            serialized_result_data["result"] = serialize_langchain_result(result_value)
        output = {
            "tool": tool_name,
            "test_type": test_type,
            "timestamp": timestamp,
            "domain": domain,
            "result": serialized_result_data
        }
        with open(filepath, 'w') as f:
            json.dump(output, f, indent=2, default=str, ensure_ascii=False)
    else:
        # General (standalone/crewai/other) case: Save VERBATIM, no wrappers, direct serialization
        serialized_result = serialize_object(result_data)
        with open(filepath, 'w') as f:
            json.dump(serialized_result, f, indent=2, cls=CustomJSONEncoder, ensure_ascii=False)
    
    return filepath

