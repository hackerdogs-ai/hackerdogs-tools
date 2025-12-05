"""
Helper function to extract actual tool output from CrewAI result object.
"""
import json
from typing import Any, Dict, Optional


def extract_tool_output_from_crewai_result(result: Any) -> Dict[str, Any]:
    """
    Extract actual tool output from CrewAI result object.
    
    CrewAI result has structure:
    - result.raw: Raw string output
    - result.tasks_output: List of TaskOutput objects
    - result.tasks_output[0].messages: List of messages (may contain tool output)
    - result.tasks_output[0].raw: Raw task output
    
    Args:
        result: CrewAI result object from crew.kickoff()
        
    Returns:
        Dictionary with:
        - tool_output_json: Parsed JSON from tool (if found)
        - tool_output: Raw tool output string (if JSON not found)
        - raw_result: String representation of full result
    """
    tool_output_json = None
    tool_output = None
    raw_result = str(result)[:500] if result else None
    
    # Try to extract from tasks_output messages
    if hasattr(result, 'tasks_output') and result.tasks_output:
        for task_output in result.tasks_output:
            # Check messages for tool output
            if hasattr(task_output, 'messages') and task_output.messages:
                for msg in task_output.messages:
                    # Look for tool output in message content
                    content = None
                    if hasattr(msg, 'content'):
                        content = msg.content
                    elif isinstance(msg, dict):
                        content = msg.get('content')
                    elif isinstance(msg, str):
                        content = msg
                    
                    if content and isinstance(content, str):
                        # Try to parse JSON from content
                        try:
                            parsed = json.loads(content)
                            if isinstance(parsed, dict) and parsed.get('status'):
                                tool_output_json = parsed
                                break
                        except (json.JSONDecodeError, AttributeError, TypeError):
                            # Not JSON, might be tool output text
                            if not tool_output:
                                tool_output = content[:2000]
            
            # Check raw task output
            if not tool_output_json and hasattr(task_output, 'raw') and task_output.raw:
                try:
                    parsed = json.loads(task_output.raw)
                    if isinstance(parsed, dict) and parsed.get('status'):
                        tool_output_json = parsed
                except (json.JSONDecodeError, AttributeError, TypeError):
                    if not tool_output:
                        tool_output = task_output.raw[:2000]
    
    # Fallback to raw output if no JSON found
    if not tool_output_json and hasattr(result, 'raw') and result.raw:
        raw_output = result.raw
        # Try to parse JSON from raw output
        try:
            tool_output_json = json.loads(raw_output)
        except (json.JSONDecodeError, AttributeError, TypeError):
            if not tool_output:
                tool_output = raw_output[:2000]
    
    return {
        "tool_output_json": tool_output_json,
        "tool_output": tool_output,
        "raw_result": raw_result
    }

