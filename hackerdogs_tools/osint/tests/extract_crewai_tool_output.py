"""
Helper function to extract actual tool output from CrewAI result object.
"""
import json
import re
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


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
    
    # Debug logging (only if DEBUG level enabled)
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug(f"DEBUG: result type: {type(result)}")
        logger.debug(f"DEBUG: result attributes: {[x for x in dir(result) if not x.startswith('_')]}")
        
        if hasattr(result, 'tasks_output') and result.tasks_output:
            logger.debug(f"DEBUG: tasks_output count: {len(result.tasks_output)}")
            for i, task in enumerate(result.tasks_output):
                logger.debug(f"DEBUG: Task {i} type: {type(task)}")
                if hasattr(task, 'messages'):
                    logger.debug(f"DEBUG: Task {i} messages count: {len(task.messages)}")
                    for j, msg in enumerate(task.messages):
                        msg_type = type(msg).__name__
                        logger.debug(f"DEBUG: Task {i}, Message {j} type: {msg_type}")
                        if hasattr(msg, 'content'):
                            content_preview = str(msg.content)[:200]
                            logger.debug(f"DEBUG: Task {i}, Message {j} content: {content_preview}")
    
    # System prompt phrases to skip
    skip_phrases = [
        "You are",
        "Your personal goal is",
        "You ONLY have access",
        "IMPORTANT: Use the following format"
    ]
    
    # Try to extract from tasks_output messages
    if hasattr(result, 'tasks_output') and result.tasks_output:
        for task_output in result.tasks_output:
            # Check messages for tool output
            if hasattr(task_output, 'messages') and task_output.messages:
                for msg in task_output.messages:
                    # Determine message type
                    msg_type = type(msg).__name__ if hasattr(msg, '__class__') else str(type(msg))
                    
                    # Check if this is a tool-related message
                    is_tool_message = (
                        'Tool' in msg_type or
                        'tool' in msg_type.lower() or
                        (hasattr(msg, 'tool_calls') and msg.tool_calls) or
                        (hasattr(msg, 'name') and msg.name)  # Tool messages often have a 'name' attribute
                    )
                    
                    # Look for tool output in message content
                    content = None
                    if hasattr(msg, 'content'):
                        content = msg.content
                    elif isinstance(msg, dict):
                        content = msg.get('content')
                    elif isinstance(msg, str):
                        content = msg
                    
                    if not content:
                        continue
                    
                    if isinstance(content, str):
                        # Skip if content looks like system prompt or instructions
                        if any(phrase in content[:500] for phrase in skip_phrases):
                            continue  # Skip system prompts
                        
                        # Try to parse JSON from content
                        try:
                            parsed = json.loads(content)
                            if isinstance(parsed, dict) and parsed.get('status'):
                                tool_output_json = parsed
                                break
                        except (json.JSONDecodeError, AttributeError, TypeError):
                            # Not JSON - but might be tool output text
                            # Only save if it's a tool message type
                            if is_tool_message and not tool_output:
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
            # Not valid JSON - try to extract JSON from within the text
            # Pattern 1: Look for JSON objects with 'status' field
            json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*"status"[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
            matches = re.finditer(json_pattern, raw_output, re.DOTALL)
            
            for match in matches:
                try:
                    parsed = json.loads(match.group())
                    if isinstance(parsed, dict) and parsed.get('status'):
                        tool_output_json = parsed
                        break
                except (json.JSONDecodeError, ValueError):
                    continue
            
            # Pattern 2: Look for JSON between backticks (common in agent responses)
            if not tool_output_json:
                code_block_pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
                code_matches = re.finditer(code_block_pattern, raw_output, re.DOTALL)
                
                for match in code_matches:
                    try:
                        parsed = json.loads(match.group(1))
                        if isinstance(parsed, dict) and parsed.get('status'):
                            tool_output_json = parsed
                            break
                    except (json.JSONDecodeError, ValueError):
                        continue
            
            # Pattern 3: Look for JSON-like structures (looser pattern)
            if not tool_output_json:
                # Find any { ... } that might be JSON
                brace_pattern = r'\{[^{}]*"status"[^{}]*\}'
                brace_matches = re.finditer(brace_pattern, raw_output, re.DOTALL)
                
                for match in brace_matches:
                    try:
                        # Try to parse with more lenient approach
                        json_str = match.group()
                        # Fix common issues: unescaped quotes, trailing commas
                        json_str = json_str.replace("'", '"')  # Single to double quotes
                        parsed = json.loads(json_str)
                        if isinstance(parsed, dict) and parsed.get('status'):
                            tool_output_json = parsed
                            break
                    except (json.JSONDecodeError, ValueError):
                        continue
            
            # Last resort: save raw output if no JSON found
            if not tool_output_json and not tool_output:
                # Only save if it doesn't look like system prompt
                if not any(phrase in raw_output[:200] for phrase in skip_phrases):
                    tool_output = raw_output[:2000]
    
    return {
        "tool_output_json": tool_output_json,
        "tool_output": tool_output,
        "raw_result": raw_result
    }

