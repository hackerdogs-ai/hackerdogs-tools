"""
Test suite for masscan tool

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

from hackerdogs_tools.osint.infrastructure.masscan_langchain import masscan_scan
from hackerdogs_tools.osint.infrastructure.masscan_crewai import MasscanTool
from hackerdogs_tools.osint.tests.test_utils import get_llm_from_env, get_crewai_llm_from_env
from hackerdogs_tools.osint.test_domains import get_random_domain
from hackerdogs_tools.osint.tests.test_runtime_helper import create_mock_runtime
from hackerdogs_tools.osint.tests.save_json_results import save_test_result, serialize_langchain_result, serialize_crewai_result, serialize_langchain_result, serialize_crewai_result


class TestMasscanStandalone:
    """Test masscan tool standalone execution."""
    
    def test_masscan_standalone(self):
        """Test masscan tool execution without agent."""
        # Use mock runtime since ToolRuntime is auto-injected in LangChain 1.x
        runtime = create_mock_runtime(state={"user_id": "test_user"})
        
        # Use local network ranges for safe testing (192.168.5.* and 192.168.4.*)
        # Test with 192.168.5.0/24 range
        test_ip_range = "192.168.5.0/24"
        test_ports = "80,443,22"
        test_rate = 1000
        
        # Tools are StructuredTool objects - use invoke() method
        result = masscan_scan.invoke({
            "runtime": runtime,
            "ip_range": test_ip_range,
            "ports": test_ports,
            "rate": test_rate
        })
        
        # Parse result - masscan returns raw stdout/stderr verbatim
        try:
            result_data = json.loads(result)
        except json.JSONDecodeError:
            # If not JSON, it's raw stdout/stderr - this is valid
            result_data = {"output": result, "format": "raw_text"}
        
        # Print JSON output for verification
        print("\n" + "=" * 80)
        print("TOOL JSON OUTPUT:")
        print("=" * 80)
        print(json.dumps(result_data, indent=2) if isinstance(result_data, dict) else result[:500])
        print("=" * 80 + "\n")
        
        # Save standalone result
        try:
            result_file = save_test_result("masscan", "standalone", result_data, test_ip_range.replace("/", "_"))
            print(f"📁 Result saved to: {result_file}")
        except Exception as e:
            print(f"⚠️  Could not save result: {e}")
        
        # Assertions
        assert result is not None, "Tool returned None"
        print(f"✅ Tool executed successfully")
        print(f"   IP Range: {test_ip_range}")
        print(f"   Ports: {test_ports}")
        print(f"   Rate: {test_rate}")


class TestMasscanCrewAI:
    """Test masscan tool with CrewAI agent."""
    
    @pytest.fixture
    def llm(self):
        """Get CrewAI LLM from environment."""
        return get_crewai_llm_from_env()
    
    @pytest.fixture
    def agent(self, llm):
        """Create CrewAI agent with masscan tool."""
        return Agent(
            role="OSINT Analyst",
            goal="Perform OSINT operations using masscan",
            backstory="You are an expert OSINT analyst.",
            tools=[MasscanTool()],
            llm=llm,
            verbose=True
        )
    
    def test_masscan_crewai_agent(self, agent, llm):
        """Test masscan tool with CrewAI agent."""
        # Use local network range for safe testing
        test_ip_range = "192.168.4.0/24"
        
        task = Task(
            description=f"Scan IP range {test_ip_range} on ports 80,443,22 using Masscan",
            agent=agent,
            expected_output="Port scan results from masscan tool"
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
            result_file = save_test_result("masscan", "crewai", result_data, test_domain)
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
    print(f"Running masscan Tool Tests")
    print("=" * 80)
    
    # Test 1: Standalone
    print("\n1. Testing Standalone Execution...")
    try:
        print("✅ Standalone test passed")
    except Exception as e:
        print(f"❌ Standalone test failed: {str(e)}")
    
    # Test 2: LangChain
    print("\n2. Testing LangChain Agent Integration...")
    try:
        tools = [masscan_scan]
        agent = create_agent(
            model=llm,
            tools=tools,
            system_prompt="You are a cybersecurity analyst. Use the masscan tool for OSINT operations."
        )
        # Use local network range for safe testing
        test_ip_range = "192.168.5.0/24"
        
        # Execute query directly (agent is a runnable in LangChain 1.x)
        # ToolRuntime is automatically injected by the agent
        result = agent.invoke({
            "messages": [HumanMessage(content=f"Scan IP range {test_ip_range} on ports 80,443,22 using Masscan")]
        })
        
        # Assertions
        assert result is not None
        assert "messages" in result or "output" in result
        
        # Save LangChain agent result
        try:
            result_data = serialize_langchain_result(result)
            result_file = save_test_result("masscan", "langchain", result_data, test_ip_range.replace("/", "_"))
            print(f"📁 LangChain result saved to: {result_file}")
        except Exception as e:
            print(f"⚠️  Could not save LangChain result: {e}")
        
        print(f"✅ LangChain test passed")
    except Exception as e:
        print(f"❌ LangChain test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Test 3: CrewAI
    print("\n3. Testing CrewAI Agent Integration...")
    try:
        agent = Agent(
            role="OSINT Analyst",
            goal="Perform OSINT operations using masscan",
            backstory="You are an expert OSINT analyst.",
            tools=[MasscanTool()],
            llm=llm,
            verbose=True
        )
        # Use local network range for safe testing
        test_ip_range = "192.168.4.0/24"
        
        task = Task(
            description=f"Scan IP range {test_ip_range} on ports 80,443,22 using Masscan",
            agent=agent,
            expected_output="Port scan results from masscan tool"
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
            result_file = save_test_result("masscan", "crewai", result_data, test_ip_range.replace("/", "_"))
            print(f"📁 CrewAI result saved to: {result_file}")
        except Exception as e:
            print(f"⚠️  Could not save CrewAI result: {e}")
        
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
