"""
Test suite for onionsearch tool

Tests:
1. Standalone tool execution
2. LangChain agent integration
3. CrewAI agent integration
"""

import pytest
import json
import os
import sys
from pathlib import Path

# Add project root to path for direct execution
project_root = Path(__file__).parent.parent.parent.parent.parent.resolve()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from crewai import Agent, Task, Crew

from hackerdogs_tools.osint.content.onionsearch_langchain import onionsearch_search
from hackerdogs_tools.osint.content.onionsearch_crewai import OnionSearchTool
from hackerdogs_tools.osint.tests.test_utils import get_llm_from_env, get_crewai_llm_from_env
from hackerdogs_tools.osint.test_domains import get_random_domain
from hackerdogs_tools.osint.test_identity_data import get_random_email
from hackerdogs_tools.osint.tests.test_runtime_helper import create_mock_runtime
from hackerdogs_tools.osint.tests.save_json_results import save_test_result, serialize_langchain_result, serialize_crewai_result


class TestOnionsearchStandalone:
    """Test onionsearch tool standalone execution."""
    
    def test_onionsearch_standalone(self):
        """Test onionsearch tool execution without agent."""
        # Use mock runtime since ToolRuntime is auto-injected in LangChain 1.x
        runtime = create_mock_runtime(state={"user_id": "test_user"})
        
        # Use a random domain for testing (Dark Web searches can be slow)
        test_query = get_random_domain()
        
        # Tools are StructuredTool objects - use invoke() method
        result = onionsearch_search.invoke({
            "runtime": runtime,
            "query": test_query,
            "limit": 1,  # Small limit for testing
            "output_format": "json"
        })
        
        # OnionSearch returns JSON string (or CSV if output_format="csv")
        # Try to parse as JSON first
        try:
            result_data = json.loads(result)
        except json.JSONDecodeError:
            # If not JSON, might be CSV or error message
            result_data = {"raw_output": result}
        
        # Print JSON output for verification
        print("\n" + "=" * 80)
        print("TOOL JSON OUTPUT:")
        print("=" * 80)
        print(json.dumps(result_data, indent=2))
        print("=" * 80 + "\n")
        
        # Save result
        try:
            result_file = save_test_result("onionsearch", "standalone", result_data, test_query)
            print(f"📁 JSON result saved to: {result_file}")
        except Exception as e:
            print(f"⚠️  Could not save result: {e}")
        
        # Basic assertions
        assert result is not None, "Result should not be None"
        assert isinstance(result, str), "Result should be a string"


class TestOnionsearchCrewAI:
    """Test onionsearch tool with CrewAI agent."""
    
    @pytest.fixture
    def llm(self):
        """Get CrewAI LLM from environment."""
        return get_crewai_llm_from_env()
    
    @pytest.fixture
    def agent(self, llm):
        """Create CrewAI agent with onionsearch tool."""
        return Agent(
            role="OSINT Analyst",
            goal="Perform OSINT operations using onionsearch",
            backstory="You are an expert OSINT analyst.",
            tools=[OnionSearchTool()],
            llm=llm,
            verbose=True
        )
    
    def test_onionsearch_crewai_agent(self, agent, llm):
        """Test onionsearch tool with CrewAI agent."""
        # Use a random domain for testing (Dark Web searches can be slow)
        test_query = get_random_domain()
        
        task = Task(
            description=f"Search for '{test_query}' on Dark Web using Onionsearch",
            agent=agent,
            expected_output="Results from onionsearch tool"
        )
        
        crew = Crew(
            agents=[agent],
            tasks=[task],
            llm=llm,
            verbose=True
        )
        
        # Execute task
        result = crew.kickoff()
        
        # Assertions
        assert result is not None, "CrewAI returned None"
        # Save CrewAI agent result
        try:
            result_data = serialize_crewai_result(result) if result else None
            result_file = save_test_result("onionsearch", "crewai", result_data, test_query)
            print(f"📁 CrewAI result saved to: {result_file}")
        except Exception as e:
            print(f"⚠️  Could not save CrewAI result: {e}")
        
                
        # Print CrewAI result for verification
        print("\n" + "=" * 80)
        print("CREWAI AGENT RESULT:")
        print("=" * 80)
        print(str(result)[:500])
        print("=" * 80 + "\n")


def run_all_tests():
    """Run all three test scenarios."""
    print("=" * 80)
    print(f"Running onionsearch Tool Tests")
    print("=" * 80)
    
    # Test 1: Standalone
    print("\n1. Testing Standalone Execution...")
    try:
        test = TestOnionsearchStandalone()
        test.test_onionsearch_standalone()
        print("✅ Standalone test passed")
    except Exception as e:
        print(f"❌ Standalone test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Test 2: LangChain
    print("\n2. Testing LangChain Agent Integration...")
    try:
        # Create agent directly (not using pytest fixtures)
        llm = get_llm_from_env()
        tools = [onionsearch_search]
        agent = create_agent(
            model=llm,
            tools=tools,
            system_prompt="You are a cybersecurity analyst. Use the onionsearch tool for Dark Web searches."
        )
        # Use a random domain for testing (Dark Web searches can be slow)
        test_query = get_random_domain()
        
        # Execute query directly (agent is a runnable in LangChain 1.x)
        # ToolRuntime is automatically injected by the agent
        result = agent.invoke({
            "messages": [HumanMessage(content=f"Search for '{test_query}' on Dark Web using Onionsearch")]
        })
        
        # Assertions
        assert result is not None
        assert "messages" in result or "output" in result
        
        # Save LangChain agent result
        try:
            result_data = serialize_langchain_result(result)
            result_file = save_test_result("onionsearch", "langchain", result_data, test_query)
            print(f"📁 LangChain result saved to: {result_file}")
        except Exception as e:
            print(f"⚠️  Could not save LangChain result: {e}")
            import traceback
            traceback.print_exc()
        
        print(f"✅ LangChain test passed")
    except Exception as e:
        print(f"❌ LangChain test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Test 3: CrewAI
    print("\n3. Testing CrewAI Agent Integration...")
    try:
        # Create LLM and agent directly (not using pytest fixtures)
        llm = get_crewai_llm_from_env()
        agent = Agent(
            role="OSINT Analyst",
            goal="Perform OSINT operations using onionsearch",
            backstory="You are an expert OSINT analyst.",
            tools=[OnionSearchTool()],
            llm=llm,
            verbose=True
        )
        # Use a random domain for testing (Dark Web searches can be slow)
        test_query = get_random_domain()
        
        task = Task(
            description=f"Search for '{test_query}' on Dark Web using Onionsearch",
            agent=agent,
            expected_output="Results from onionsearch tool"
        )
        
        crew = Crew(
            agents=[agent],
            tasks=[task],
            llm=llm,
            verbose=True
        )
        
        # Execute task
        result = crew.kickoff()
        
        # Assertions
        assert result is not None
        
        # Save CrewAI agent result
        try:
            result_data = serialize_crewai_result(result) if result else None
            result_file = save_test_result("onionsearch", "crewai", result_data, test_query)
            print(f"📁 CrewAI result saved to: {result_file}")
        except Exception as e:
            print(f"⚠️  Could not save CrewAI result: {e}")
            import traceback
            traceback.print_exc()
        
        print(f"✅ CrewAI test passed")
    except Exception as e:
        print(f"❌ CrewAI test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("All tests completed!")
    print("=" * 80)


if __name__ == "__main__":
    run_all_tests()
