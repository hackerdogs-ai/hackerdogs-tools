"""
Test suite for maigret tool

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

from hackerdogs_tools.osint.identity.maigret_langchain import maigret_search
from hackerdogs_tools.osint.identity.maigret_crewai import MaigretTool
from hackerdogs_tools.osint.tests.test_utils import get_llm_from_env, get_crewai_llm_from_env
from hackerdogs_tools.osint.test_domains import get_random_domain
from hackerdogs_tools.osint.test_identity_data import get_random_username
from hackerdogs_tools.osint.tests.test_runtime_helper import create_mock_runtime
from hackerdogs_tools.osint.tests.save_json_results import save_test_result, serialize_langchain_result, serialize_crewai_result, serialize_langchain_result, serialize_crewai_result


class TestMaigretStandalone:
    """Test maigret tool standalone execution."""
    
    def test_maigret_standalone(self):
        """Test maigret tool execution without agent."""
        # Use mock runtime since ToolRuntime is auto-injected in LangChain 1.x
        runtime = create_mock_runtime(state={"user_id": "test_user"})
        
        # Use a random realistic username (maigret searches for usernames, not domains)
        test_username = get_random_username()
        
        # Tools are StructuredTool objects - use invoke() method
        # Maigret requires "usernames" parameter (list), not "username"
        result = maigret_search.invoke({
            "runtime": runtime,
            "usernames": [test_username],  # Must be a list
            "report_format": "json",
            "json_type": "simple"
        })
        
        # Parse result
        result_data = json.loads(result)
        
        # Print JSON output for verification
        print("\n" + "=" * 80)
        print("TOOL JSON OUTPUT:")
        print("=" * 80)
        print(json.dumps(result_data, indent=2))
        print("=" * 80 + "\n")
        
        # Save JSON result to file - VERBATIM without wrappers
        try:
            result_file = save_test_result("maigret", "standalone", result_data, test_username)
            print(f"📁 JSON result saved to: {result_file}")
            # Verify file exists
            if not os.path.exists(result_file):
                print(f"⚠️  WARNING: File was not created: {result_file}")
            else:
                file_size = os.path.getsize(result_file)
                print(f"✅ File verified: {result_file} ({file_size} bytes)")
        except Exception as e:
            print(f"❌ ERROR: Failed to save result file: {e}")
            import traceback
            traceback.print_exc()
            raise
        
        # Assertions
        assert "status" in result_data, f"Missing 'status' in result: {result_data}"
        assert result_data["status"] in ["success", "error"], f"Invalid status: {result_data.get('status')}"
        
        if result_data["status"] == "success":
            assert "usernames" in result_data, f"Missing 'usernames' in result: {result_data}"
            print(f"✅ Tool executed successfully")
            print(f"   Usernames: {result_data.get('usernames')}")
            print(f"   Execution method: {result_data.get('execution_method', 'docker')}")
        else:
            # If error, should have message
            assert "message" in result_data, f"Error status but no message: {result_data}"
            print(f"⚠️  Tool returned error: {result_data.get('message')}")


class TestMaigretLangChain:
    """Test maigret tool with LangChain agent."""
    
    @pytest.fixture
    def llm(self):
        """Get LLM from environment."""
        return get_llm_from_env()
    
    @pytest.fixture
    def agent(self, llm):
        """Create LangChain agent with maigret tool."""
        tools = [maigret_search]
        agent = create_agent(
            model=llm,
            tools=tools,
            system_prompt="You are a cybersecurity analyst. Use the maigret tool for advanced username search."
        )
        return agent
    
    def test_maigret_langchain_agent(self, agent):
        """Test maigret tool with LangChain agent."""
        # Use a random realistic username (maigret searches for usernames)
        test_username = get_random_username()
        
        # Execute query directly (agent is a runnable in LangChain 1.x)
        # ToolRuntime is automatically injected by the agent
        result = agent.invoke({
            "messages": [HumanMessage(content=f"Search for username {test_username} using Maigret")]
        })
        
        # Assertions
        assert result is not None, "Agent returned None"
        assert "messages" in result or "output" in result, f"Invalid agent result structure: {result}"
        
        # Save LangChain agent result - complete result as-is, no truncation, no decoration
        try:
            result_data = serialize_langchain_result(result)
            result_file = save_test_result("maigret", "langchain", result_data, test_username)
            print(f"📁 LangChain result saved to: {result_file}")
            # Verify file exists
            if not os.path.exists(result_file):
                print(f"⚠️  WARNING: File was not created: {result_file}")
            else:
                file_size = os.path.getsize(result_file)
                print(f"✅ File verified: {result_file} ({file_size} bytes)")
        except Exception as e:
            print(f"❌ ERROR: Could not save LangChain result: {e}")
            import traceback
            traceback.print_exc()
            raise
        
                
        # Print agent result for verification
        print("\n" + "=" * 80)
        print("LANGCHAIN AGENT RESULT:")
        print("=" * 80)
        if "messages" in result:
            for msg in result["messages"]:
                print(f"  {msg.__class__.__name__}: {str(msg.content)[:200]}")
        print("=" * 80 + "\n")


class TestMaigretCrewAI:
    """Test maigret tool with CrewAI agent."""
    
    @pytest.fixture
    def llm(self):
        """Get CrewAI LLM from environment."""
        return get_crewai_llm_from_env()
    
    @pytest.fixture
    def agent(self, llm):
        """Create CrewAI agent with maigret tool."""
        return Agent(
            role="OSINT Analyst",
            goal="Perform OSINT operations using maigret",
            backstory="You are an expert OSINT analyst.",
            tools=[MaigretTool()],
            llm=llm,
            verbose=True
        )
    
    def test_maigret_crewai_agent(self, agent, llm):
        """Test maigret tool with CrewAI agent."""
        # Use a random realistic username (maigret searches for usernames)
        test_username = get_random_username()
        
        task = Task(
            description=f"Search for username {test_username} using Maigret",
            agent=agent,
            expected_output="Username search results from maigret tool"
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
        
        # Save CrewAI agent result - complete result as-is
        try:
            result_data = serialize_crewai_result(result) if result else None
            if result_data is None:
                print("⚠️  WARNING: result_data is None, cannot save")
            else:
                result_file = save_test_result("maigret", "crewai", result_data, test_username)
                print(f"📁 CrewAI result saved to: {result_file}")
                # Verify file exists
                if not os.path.exists(result_file):
                    print(f"⚠️  WARNING: File was not created: {result_file}")
                else:
                    file_size = os.path.getsize(result_file)
                    print(f"✅ File verified: {result_file} ({file_size} bytes)")
        except Exception as e:
            print(f"❌ ERROR: Could not save CrewAI result: {e}")
            import traceback
            traceback.print_exc()
            raise
        
                
        # Print CrewAI result for verification
        print("\n" + "=" * 80)
        print("CREWAI AGENT RESULT:")
        print("=" * 80)
        print(str(result)[:500])
        print("=" * 80 + "\n")


def run_all_tests():
    """Run all three test scenarios."""
    print("=" * 80)
    print(f"Running maigret Tool Tests")
    print("=" * 80)
    
    # Test 1: Standalone
    print("\n1. Testing Standalone Execution...")
    try:
        test = TestMaigretStandalone()
        test.test_maigret_standalone()
        print("✅ Standalone test passed")
    except Exception as e:
        print(f"❌ Standalone test failed: {str(e)}")
    
    # Test 2: LangChain
    print("\n2. Testing LangChain Agent Integration...")
    try:
        # Create agent directly (not using pytest fixtures)
        llm = get_llm_from_env()
        tools = [maigret_search]
        agent = create_agent(
            model=llm,
            tools=tools,
            system_prompt="You are a cybersecurity analyst. Use the maigret tool for advanced username search."
        )
        # Use a random realistic username (maigret searches for usernames)
        test_username = get_random_username()
        
        # Execute query directly (agent is a runnable in LangChain 1.x)
        # ToolRuntime is automatically injected by the agent
        result = agent.invoke({
            "messages": [HumanMessage(content=f"Search for username {test_username} using Maigret")]
        })
        
        # Assertions
        assert result is not None
        assert "messages" in result or "output" in result
        
        # Save LangChain agent result - complete result as-is, no truncation, no decoration
        try:
            result_data = serialize_langchain_result(result)
            result_file = save_test_result("maigret", "langchain", result_data, test_username)
            print(f"📁 LangChain result saved to: {result_file}")
            # Verify file exists
            if not os.path.exists(result_file):
                print(f"⚠️  WARNING: File was not created: {result_file}")
            else:
                file_size = os.path.getsize(result_file)
                print(f"✅ File verified: {result_file} ({file_size} bytes)")
        except Exception as e:
            print(f"❌ ERROR: Could not save LangChain result: {e}")
            import traceback
            traceback.print_exc()
            raise
        
        print(f"✅ LangChain test passed")
    except Exception as e:
        print(f"❌ LangChain test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Test 3: CrewAI
    print("\n3. Testing CrewAI Agent Integration...")
    try:
        # Create agent directly (not using pytest fixtures)
        llm = get_crewai_llm_from_env()
        agent = Agent(
            role="OSINT Analyst",
            goal="Perform OSINT operations using maigret",
            backstory="You are an expert OSINT analyst.",
            tools=[MaigretTool()],
            llm=llm,
            verbose=True
        )
        # Use a random realistic username (maigret searches for usernames)
        test_username = get_random_username()
        
        task = Task(
            description=f"Search for username {test_username} using Maigret",
            agent=agent,
            expected_output="Username search results from maigret tool"
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
        
        # Save CrewAI agent result - complete result as-is
        try:
            result_data = serialize_crewai_result(result) if result else None
            if result_data is None:
                print("⚠️  WARNING: result_data is None, cannot save")
            else:
                result_file = save_test_result("maigret", "crewai", result_data, test_username)
                print(f"📁 CrewAI result saved to: {result_file}")
                # Verify file exists
                if not os.path.exists(result_file):
                    print(f"⚠️  WARNING: File was not created: {result_file}")
                else:
                    file_size = os.path.getsize(result_file)
                    print(f"✅ File verified: {result_file} ({file_size} bytes)")
        except Exception as e:
            print(f"❌ ERROR: Could not save CrewAI result: {e}")
            import traceback
            traceback.print_exc()
            raise
        
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
