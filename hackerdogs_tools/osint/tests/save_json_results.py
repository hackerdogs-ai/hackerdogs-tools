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
    
    LangChain messages are Pydantic BaseModel objects, so we can use
    model_dump() or dict() methods to serialize them properly.
    
    Args:
        message: LangChain message object (HumanMessage, AIMessage, ToolMessage, etc.)
        
    Returns:
        Dictionary representation of the message
    """
    try:
        # Try Pydantic v2 method first
        if hasattr(message, 'model_dump'):
            return message.model_dump(mode='json')
        # Fallback to Pydantic v1 method
        elif hasattr(message, 'dict'):
            return message.dict()
        # Fallback to manual extraction
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
            # Add message type
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
    
    LangChain agent results typically contain a 'messages' list with
    message objects that need proper serialization.
    
    Args:
        result: LangChain agent result (dict with 'messages' key)
        
    Returns:
        Dictionary with properly serialized messages
    """
    if not isinstance(result, dict):
        # If result is not a dict, try to convert it
        if hasattr(result, 'model_dump'):
            result = result.model_dump(mode='json')
        elif hasattr(result, 'dict'):
            result = result.dict()
        elif hasattr(result, '__dict__'):
            result = result.__dict__
        else:
            return {"raw": str(result), "type": type(result).__name__}
    
    # Create a copy to avoid modifying the original
    serialized = result.copy()
    
    # Serialize messages if present
    if "messages" in serialized and isinstance(serialized["messages"], list):
        serialized["messages"] = [
            serialize_langchain_message(msg) for msg in serialized["messages"]
        ]
    
    return serialized


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
    
    # Serialize result_data properly based on test type
    serialized_result_data = result_data.copy()
    
    # If LangChain test, serialize the result dict properly
    if test_type == "langchain" and "result" in serialized_result_data:
        result_value = serialized_result_data["result"]
        if isinstance(result_value, dict):
            serialized_result_data["result"] = serialize_langchain_result(result_value)
        elif hasattr(result_value, 'model_dump'):
            # If result is a Pydantic model, serialize it
            serialized_result_data["result"] = serialize_langchain_result(result_value)
    
    # Add metadata
    output = {
        "tool": tool_name,
        "test_type": test_type,
        "timestamp": timestamp,
        "domain": domain,
        "result": serialized_result_data
    }
    
    # Write JSON file
    # Use default=str as fallback for any remaining non-serializable objects
    with open(filepath, 'w') as f:
        json.dump(output, f, indent=2, default=str, ensure_ascii=False)  # ensure_ascii=False preserves unicode
    
    return filepath

