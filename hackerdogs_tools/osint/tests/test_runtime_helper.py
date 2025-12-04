"""
Helper for creating ToolRuntime in tests.

Note: In LangChain 1.x, ToolRuntime is automatically injected by the framework.
For standalone tests, we create a real ToolRuntime instance.
"""

from typing import Any, Dict
from unittest.mock import Mock
from langchain.tools import ToolRuntime

def create_mock_runtime(state: Dict[str, Any] = None) -> ToolRuntime:
    """
    Create a real ToolRuntime instance for testing.
    
    Args:
        state: Optional state dictionary (default: {"user_id": "test_user", "messages": []})
    
    Returns:
        ToolRuntime instance
    """
    if state is None:
        state = {"user_id": "test_user", "messages": []}
    
    # Create ToolRuntime with all required parameters
    runtime = ToolRuntime(
        state=state,
        context={},
        config={},
        stream_writer=Mock(),
        tool_call_id="test_call_123",
        store=None
    )
    
    return runtime

