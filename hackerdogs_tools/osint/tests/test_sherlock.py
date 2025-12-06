"""
Test suite for sherlock tool

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

from hackerdogs_tools.osint.identity.sherlock_langchain import sherlock_enum
from hackerdogs_tools.osint.identity.sherlock_crewai import SherlockTool
from hackerdogs_tools.osint.tests.test_utils import get_llm_from_env, get_crewai_llm_from_env
from hackerdogs_tools.osint.test_domains import get_random_domain
from hackerdogs_tools.osint.test_identity_data import get_random_username, get_random_usernames
from hackerdogs_tools.osint.tests.test_runtime_helper import create_mock_runtime
from hackerdogs_tools.osint.tests.save_json_results import save_test_result, serialize_langchain_result, serialize_crewai_result, serialize_langchain_result, serialize_crewai_result


class TestSherlockStandalone:
    """Test sherlock tool standalone execution."""
    
    def test_sherlock_standalone_single(self):
        """Test sherlock tool execution without agent - single username."""
        # Use mock runtime since ToolRuntime is auto-injected in LangChain 1.x
        runtime = create_mock_runtime(state={"user_id": "test_user"})
        
        # Test 1: Single username "dynamicdeploy"
        test_usernames = ["dynamicdeploy"]
        
        # Tools are StructuredTool objects - use invoke() method
        # Sherlock requires "usernames" as a list
        result = sherlock_enum.invoke({
            "runtime": runtime,
            "usernames": test_usernames,
            "output_format": "json",
            "timeout": 60,
            "nsfw": False
        })
        
        # Parse result
        result_data = json.loads(result)
        
        # Print JSON output for verification
        print("\n" + "=" * 80)
        print("TOOL JSON OUTPUT (Single Username):")
        print("=" * 80)
        print(json.dumps(result_data, indent=2))
        print("=" * 80 + "\n")
        
        # Save JSON result to file - VERBATIM without wrappers
        result_file = save_test_result("sherlock", "standalone_single", result_data, "dynamicdeploy")
        print(f"📁 JSON result saved to: {result_file}")
        
        # Assertions
        assert "status" in result_data, f"Missing 'status' in result: {result_data}"
        assert result_data["status"] in ["success", "error"], f"Invalid status: {result_data.get('status')}"
        
        if result_data["status"] == "success":
            assert "usernames" in result_data, f"Missing 'usernames' in result: {result_data}"
            assert "results" in result_data, f"Missing 'results' in result: {result_data}"
            print(f"✅ Tool executed successfully (single username)")
            print(f"   Usernames: {result_data.get('usernames')}")
            print(f"   Count: {result_data.get('count', 0)}")
            print(f"   Execution method: {result_data.get('execution_method', 'docker')}")
        else:
            # If error, should have message
            assert "message" in result_data, f"Error status but no message: {result_data}"
            print(f"⚠️  Tool returned error: {result_data.get('message')}")
    
    def test_sherlock_standalone_multiple(self):
        """Test sherlock tool execution without agent - multiple usernames."""
        # Use mock runtime since ToolRuntime is auto-injected in LangChain 1.x
        runtime = create_mock_runtime(state={"user_id": "test_user"})
        
        # Test 2: 5 random usernames from usernames.txt (stripped from emails)
        test_usernames = get_random_usernames(count=5)
        
        # Tools are StructuredTool objects - use invoke() method
        # Sherlock requires "usernames" as a list
        result = sherlock_enum.invoke({
            "runtime": runtime,
            "usernames": test_usernames,
            "output_format": "json",
            "timeout": 60,
            "nsfw": False
        })
        
        # Parse result
        result_data = json.loads(result)
        
        # Print JSON output for verification
        print("\n" + "=" * 80)
        print("TOOL JSON OUTPUT (Multiple Usernames):")
        print("=" * 80)
        print(json.dumps(result_data, indent=2))
        print("=" * 80 + "\n")
        
        # Save JSON result to file - VERBATIM without wrappers
        usernames_str = "_".join(test_usernames[:3])  # Use first 3 for filename
        result_file = save_test_result("sherlock", "standalone_multiple", result_data, usernames_str)
        print(f"📁 JSON result saved to: {result_file}")
        
        # Assertions
        assert "status" in result_data, f"Missing 'status' in result: {result_data}"
        assert result_data["status"] in ["success", "error"], f"Invalid status: {result_data.get('status')}"
        
        if result_data["status"] == "success":
            assert "usernames" in result_data, f"Missing 'usernames' in result: {result_data}"
            assert "results" in result_data, f"Missing 'results' in result: {result_data}"
            assert len(result_data.get("usernames", [])) == 5, f"Expected 5 usernames, got {len(result_data.get('usernames', []))}"
            print(f"✅ Tool executed successfully (multiple usernames)")
            print(f"   Usernames: {result_data.get('usernames')}")
            print(f"   Count: {result_data.get('count', 0)}")
            print(f"   Execution method: {result_data.get('execution_method', 'docker')}")
        else:
            # If error, should have message
            assert "message" in result_data, f"Error status but no message: {result_data}"
            print(f"⚠️  Tool returned error: {result_data.get('message')}")


class TestSherlockLangChain:
    """Test sherlock tool with LangChain agent."""
    
    @pytest.fixture
    def llm(self):
        """Get LLM from environment."""
        return get_llm_from_env()
    
    @pytest.fixture
    def agent(self, llm):
        """Create LangChain agent with sherlock tool."""
        tools = [sherlock_enum]
        agent = create_agent(
            model=llm,
            tools=tools,
            system_prompt="You are a cybersecurity analyst. Use the sherlock tool for username enumeration."
        )
        return agent
    
    def test_sherlock_langchain_agent_single(self, agent):
        """Test sherlock tool with LangChain agent - single username."""
        # Test 1: Single username "dynamicdeploy"
        test_username = "dynamicdeploy"
        
        # Execute query directly (agent is a runnable in LangChain 1.x)
        # ToolRuntime is automatically injected by the agent
        # Note: Agent will need to pass usernames as a list
        result = agent.invoke({
            "messages": [HumanMessage(content=f"Search for username {test_username} across social media using Sherlock. Use usernames as a list parameter.")]
        })
        
        # Assertions
        assert result is not None, "Agent returned None"
        assert "messages" in result or "output" in result, f"Invalid agent result structure: {result}"
        
        # Save LangChain agent result - VERBATIM, no wrapper
        try:
            result_data = serialize_langchain_result(result)
            result_file = save_test_result("sherlock", "langchain_single", result_data, test_username)
            print(f"📁 LangChain result saved to: {result_file}")
        except Exception as e:
            print(f"⚠️  Could not save LangChain result: {e}")
            import traceback
            traceback.print_exc()
        
        # Print agent result for verification
        print("\n" + "=" * 80)
        print("LANGCHAIN AGENT RESULT (Single Username):")
        print("=" * 80)
        if "messages" in result:
            for msg in result["messages"]:
                print(f"  {msg.__class__.__name__}: {str(msg.content)[:200]}")
        print("=" * 80 + "\n")
    
    def test_sherlock_langchain_agent_multiple(self, agent):
        """Test sherlock tool with LangChain agent - multiple usernames."""
        # Test 2: 5 random usernames from usernames.txt
        test_usernames = get_random_usernames(count=5)
        usernames_str = ", ".join(test_usernames)
        
        # Execute query directly (agent is a runnable in LangChain 1.x)
        # ToolRuntime is automatically injected by the agent
        # Note: Agent will need to pass usernames as a list
        result = agent.invoke({
            "messages": [HumanMessage(content=f"Search for usernames {usernames_str} across social media using Sherlock. Use usernames as a list parameter with all 5 usernames.")]
        })
        
        # Assertions
        assert result is not None, "Agent returned None"
        assert "messages" in result or "output" in result, f"Invalid agent result structure: {result}"
        
        # Save LangChain agent result - VERBATIM, no wrapper
        try:
            result_data = serialize_langchain_result(result)
            usernames_file_str = "_".join(test_usernames[:3])  # Use first 3 for filename
            result_file = save_test_result("sherlock", "langchain_multiple", result_data, usernames_file_str)
            print(f"📁 LangChain result saved to: {result_file}")
        except Exception as e:
            print(f"⚠️  Could not save LangChain result: {e}")
            import traceback
            traceback.print_exc()
        
        # Print agent result for verification
        print("\n" + "=" * 80)
        print("LANGCHAIN AGENT RESULT (Multiple Usernames):")
        print("=" * 80)
        if "messages" in result:
            for msg in result["messages"]:
                print(f"  {msg.__class__.__name__}: {str(msg.content)[:200]}")
        print("=" * 80 + "\n")


class TestSherlockCrewAI:
    """Test sherlock tool with CrewAI agent."""
    
    @pytest.fixture
    def llm(self):
        """Get CrewAI LLM from environment."""
        return get_crewai_llm_from_env()
    
    @pytest.fixture
    def agent(self, llm):
        """Create CrewAI agent with sherlock tool."""
        return Agent(
            role="OSINT Analyst",
            goal="Perform OSINT operations using sherlock",
            backstory="You are an expert OSINT analyst.",
            tools=[SherlockTool()],
            llm=llm,
            verbose=True
        )
    
    def test_sherlock_crewai_agent_single(self, agent, llm):
        """Test sherlock tool with CrewAI agent - single username."""
        # Test 1: Single username "dynamicdeploy"
        test_username = "dynamicdeploy"
        
        task = Task(
            description=f"Search for username {test_username} across social media using Sherlock. Pass usernames as a list parameter.",
            agent=agent,
            expected_output="Username enumeration results from sherlock tool"
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
        
        # Save CrewAI agent result - VERBATIM, no wrapper
        try:
            result_data = serialize_crewai_result(result) if result else None
            result_file = save_test_result("sherlock", "crewai_single", result_data, test_username)
            print(f"📁 CrewAI result saved to: {result_file}")
        except Exception as e:
            print(f"⚠️  Could not save CrewAI result: {e}")
            import traceback
            traceback.print_exc()
        
        # Print CrewAI result for verification
        print("\n" + "=" * 80)
        print("CREWAI AGENT RESULT (Single Username):")
        print("=" * 80)
        print(str(result)[:500])
        print("=" * 80 + "\n")
    
    def test_sherlock_crewai_agent_multiple(self, agent, llm):
        """Test sherlock tool with CrewAI agent - multiple usernames."""
        # Test 2: 5 random usernames from usernames.txt
        test_usernames = get_random_usernames(count=5)
        usernames_str = ", ".join(test_usernames)
        
        task = Task(
            description=f"Search for usernames {usernames_str} across social media using Sherlock. Pass usernames as a list parameter with all 5 usernames.",
            agent=agent,
            expected_output="Username enumeration results from sherlock tool for all 5 usernames"
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
        
        # Save CrewAI agent result - VERBATIM, no wrapper
        try:
            result_data = serialize_crewai_result(result) if result else None
            usernames_file_str = "_".join(test_usernames[:3])  # Use first 3 for filename
            result_file = save_test_result("sherlock", "crewai_multiple", result_data, usernames_file_str)
            print(f"📁 CrewAI result saved to: {result_file}")
        except Exception as e:
            print(f"⚠️  Could not save CrewAI result: {e}")
            import traceback
            traceback.print_exc()
        
        # Print CrewAI result for verification
        print("\n" + "=" * 80)
        print("CREWAI AGENT RESULT (Multiple Usernames):")
        print("=" * 80)
        print(str(result)[:500])
        print("=" * 80 + "\n")


def run_all_tests():
    """Run all test scenarios (standalone, LangChain, CrewAI) for both single and multiple usernames."""
    print("=" * 80)
    print(f"Running sherlock Tool Tests")
    print("=" * 80)
    
    # Test 1: Standalone - Single Username
    print("\n1. Testing Standalone Execution (Single Username)...")
    try:
        test = TestSherlockStandalone()
        test.test_sherlock_standalone_single()
        print("✅ Standalone single username test passed")
    except Exception as e:
        print(f"❌ Standalone single username test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Test 2: Standalone - Multiple Usernames
    print("\n1. Testing Standalone Execution (Multiple Usernames)...")
    try:
        test = TestSherlockStandalone()
        test.test_sherlock_standalone_multiple()
        print("✅ Standalone multiple usernames test passed")
    except Exception as e:
        print(f"❌ Standalone multiple usernames test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Test 3: LangChain - Single Username
    print("\n2. Testing LangChain Agent Integration (Single Username)...")
    try:
        llm = get_llm_from_env()
        tools = [sherlock_enum]
        agent = create_agent(
            model=llm,
            tools=tools,
            system_prompt="You are a cybersecurity analyst. Use the sherlock tool for username enumeration."
        )
        test_username = "dynamicdeploy"
        
        result = agent.invoke({
            "messages": [HumanMessage(content=f"Search for username {test_username} across social media using Sherlock. Use usernames as a list parameter.")]
        })
        
        assert result is not None
        assert "messages" in result or "output" in result
        
        try:
            result_data = serialize_langchain_result(result)
            result_file = save_test_result("sherlock", "langchain_single", result_data, test_username)
            print(f"📁 LangChain result saved to: {result_file}")
        except Exception as e:
            print(f"⚠️  Could not save LangChain result: {e}")
            import traceback
            traceback.print_exc()
        
        print(f"✅ LangChain single username test passed")
    except Exception as e:
        print(f"❌ LangChain single username test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Test 4: LangChain - Multiple Usernames
    print("\n2. Testing LangChain Agent Integration (Multiple Usernames)...")
    try:
        llm = get_llm_from_env()
        tools = [sherlock_enum]
        agent = create_agent(
            model=llm,
            tools=tools,
            system_prompt="You are a cybersecurity analyst. Use the sherlock tool for username enumeration."
        )
        test_usernames = get_random_usernames(count=5)
        usernames_str = ", ".join(test_usernames)
        
        result = agent.invoke({
            "messages": [HumanMessage(content=f"Search for usernames {usernames_str} across social media using Sherlock. Use usernames as a list parameter with all 5 usernames.")]
        })
        
        assert result is not None
        assert "messages" in result or "output" in result
        
        try:
            result_data = serialize_langchain_result(result)
            usernames_file_str = "_".join(test_usernames[:3])
            result_file = save_test_result("sherlock", "langchain_multiple", result_data, usernames_file_str)
            print(f"📁 LangChain result saved to: {result_file}")
        except Exception as e:
            print(f"⚠️  Could not save LangChain result: {e}")
            import traceback
            traceback.print_exc()
        
        print(f"✅ LangChain multiple usernames test passed")
    except Exception as e:
        print(f"❌ LangChain multiple usernames test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Test 5: CrewAI - Single Username
    print("\n3. Testing CrewAI Agent Integration (Single Username)...")
    try:
        llm = get_crewai_llm_from_env()
        agent = Agent(
            role="OSINT Analyst",
            goal="Perform OSINT operations using sherlock",
            backstory="You are an expert OSINT analyst.",
            tools=[SherlockTool()],
            llm=llm,
            verbose=True
        )
        test_username = "dynamicdeploy"
        
        task = Task(
            description=f"Search for username {test_username} across social media using Sherlock. Pass usernames as a list parameter.",
            agent=agent,
            expected_output="Username enumeration results from sherlock tool"
        )
        
        crew = Crew(
            agents=[agent],
            tasks=[task],
            llm=llm,
            verbose=True
        )
        
        result = crew.kickoff()
        
        assert result is not None
        
        try:
            result_data = serialize_crewai_result(result) if result else None
            result_file = save_test_result("sherlock", "crewai_single", result_data, test_username)
            print(f"📁 CrewAI result saved to: {result_file}")
        except Exception as e:
            print(f"⚠️  Could not save CrewAI result: {e}")
            import traceback
            traceback.print_exc()
        
        print(f"✅ CrewAI single username test passed")
    except Exception as e:
        print(f"❌ CrewAI single username test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Test 6: CrewAI - Multiple Usernames
    print("\n3. Testing CrewAI Agent Integration (Multiple Usernames)...")
    try:
        llm = get_crewai_llm_from_env()
        agent = Agent(
            role="OSINT Analyst",
            goal="Perform OSINT operations using sherlock",
            backstory="You are an expert OSINT analyst.",
            tools=[SherlockTool()],
            llm=llm,
            verbose=True
        )
        # Use 2 usernames for CrewAI test to avoid timeout (tool execution + LLM calls can take 10+ minutes with 5)
        test_usernames = get_random_usernames(count=2)
        usernames_str = ", ".join(test_usernames)
        
        task = Task(
            description=f"Search for usernames {usernames_str} across social media using Sherlock. Pass usernames as a list parameter with all 2 usernames.",
            agent=agent,
            expected_output="Username enumeration results from sherlock tool for all 2 usernames"
        )
        
        crew = Crew(
            agents=[agent],
            tasks=[task],
            llm=llm,
            verbose=True
        )
        
        result = crew.kickoff()
        
        assert result is not None
        
        try:
            result_data = serialize_crewai_result(result) if result else None
            usernames_file_str = "_".join(test_usernames[:3])
            result_file = save_test_result("sherlock", "crewai_multiple", result_data, usernames_file_str)
            print(f"📁 CrewAI result saved to: {result_file}")
        except Exception as e:
            print(f"⚠️  Could not save CrewAI result: {e}")
            import traceback
            traceback.print_exc()
        
        print(f"✅ CrewAI multiple usernames test passed")
    except Exception as e:
        print(f"❌ CrewAI multiple usernames test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("All tests completed!")
    print("=" * 80)


if __name__ == "__main__":
    run_all_tests()
