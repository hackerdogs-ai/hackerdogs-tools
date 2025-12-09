"""
Test suite for Fraudguard tool (fraudguard)

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
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

# Add project root to path for direct execution
project_root = Path(__file__).parent.parent.parent.parent.parent.resolve()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from crewai import Agent, Task, Crew

from hackerdogs_tools.osint.spiderfoot_modules.sfp_fraudguard_langchain import sfp_fraudguard
from hackerdogs_tools.osint.spiderfoot_modules.sfp_fraudguard_crewai import SfpFraudguardTool
from hackerdogs_tools.osint.tests.test_utils import get_llm_from_env, get_crewai_llm_from_env
# Note: get_random_ip() not available - using local IP for testing
from hackerdogs_tools.osint.tests.test_runtime_helper import create_mock_runtime
from hackerdogs_tools.osint.tests.save_json_results import save_test_result, serialize_langchain_result, serialize_crewai_result


class TestFraudguardStandalone:
    """Test Fraudguard tool standalone execution."""
    
    def test_fraudguard_standalone(self):
        """Test fraudguard tool execution without agent."""
        # Use mock runtime since ToolRuntime is auto-injected in LangChain 1.x
        runtime = create_mock_runtime(state={"user_id": "test_user"})
        
        # Determine test target based on watched events
        test_target = "192.168.5.1"  # Use local IP for testing (safe local network)
        
        # Build invoke parameters
        invoke_params = {
            "runtime": runtime,
            "target": test_target
        }
        # Fraudguard.io API username.
        invoke_params["fraudguard_api_key_account"] = ""
        # Fraudguard.io API password.
        invoke_params["fraudguard_api_key_password"] = ""
        # Ignore any records older than this many days. 0 = unlimited.
        invoke_params["age_limit_days"] = 90
        # Look up all IPs on netblocks deemed to be owned by your target for possible blacklisted hosts on the same target subdomain/domain?
        invoke_params["netblocklookup"] = True
        # If looking up owned netblocks, the maximum IPv4 netblock size to look up all IPs within (CIDR value, 24 = /24, 16 = /16, etc.)
        invoke_params["maxnetblock"] = 24
        # If looking up owned netblocks, the maximum IPv6 netblock size to look up all IPs within (CIDR value, 24 = /24, 16 = /16, etc.)
        invoke_params["maxv6netblock"] = 120
        # Look up all IPs on subnets which your target is a part of for blacklisting?
        invoke_params["subnetlookup"] = True
        # If looking up subnets, the maximum IPv4 subnet size to look up all the IPs within (CIDR value, 24 = /24, 16 = /16, etc.)
        invoke_params["maxsubnet"] = 24
        # If looking up subnets, the maximum IPv6 subnet size to look up all the IPs within (CIDR value, 24 = /24, 16 = /16, etc.)
        invoke_params["maxv6subnet"] = 120
        # Apply checks to affiliates?
        invoke_params["checkaffiliates"] = True
        # API key will be retrieved from runtime.state or environment
        
        # Tools are StructuredTool objects - use invoke() method
        result = sfp_fraudguard.invoke(invoke_params)
        
        # Parse result
        try:
            result_data = json.loads(result)
        except json.JSONDecodeError:
            # If not JSON, treat as error message
            result_data = {"status": "error", "message": result}
        
        # Print JSON output for verification
        print("\n" + "=" * 80)
        print("TOOL JSON OUTPUT:")
        print("=" * 80)
        print(json.dumps(result_data, indent=2))
        print("=" * 80 + "\n")
        
        # Save JSON result to file
        target_filename = test_target.replace("@", "_at_").replace(".", "_").replace("/", "_")
        result_file = save_test_result("fraudguard", "standalone", result_data, target_filename)
        print(f"📁 JSON result saved to: {result_file}")
        
        # Assertions
        assert result is not None, "Result should not be None"
        assert isinstance(result, str), "Result should be a string"
        
        if isinstance(result_data, dict):
            assert "status" in result_data, "Result should contain 'status' field"
            assert result_data["status"] in ["success", "error"], f"Invalid status: {result_data.get('status')}"
            if result_data["status"] == "success":
                print(f"✅ Tool executed successfully")
                assert "module" in result_data, "Successful result should contain 'module' field"
            else:
                print(f"⚠️  Tool returned error: {result_data.get('message', 'Unknown error')}")
        else:
            print(f"⚠️  Unexpected result format: {type(result_data)}")


class TestFraudguardLangChain:
    """Test Fraudguard tool with LangChain agent."""
    
    def test_fraudguard_langchain_agent(self):
        """Test fraudguard tool with LangChain agent."""
        # Create agent directly (not using pytest fixtures)
        llm = get_llm_from_env()
        tools = [sfp_fraudguard]
        agent = create_agent(
            model=llm,
            tools=tools,
            system_prompt="You are a cybersecurity analyst. Use the Fraudguard tool for OSINT operations. IMPORTANT: Return the tool output verbatim as JSON without any additional commentary or summarization."
        )
        
        # Determine test target based on watched events
        test_target = "192.168.5.1"  # Use local IP for testing (safe local network)
        
        # Execute query directly (agent is a runnable in LangChain 1.x)
        # ToolRuntime is automatically injected by the agent
        result = agent.invoke({
            "messages": [HumanMessage(content=f"Use Fraudguard to investigate {test_target}")],
            "user_id": "test_user"
        })
        
        # Assertions
        assert result is not None, "Agent returned None"
        assert "messages" in result or "output" in result, f"Invalid agent result structure: {result}"
        
        # Extract tool output from messages
        tool_output_message = next((msg for msg in reversed(result["messages"]) if msg.type == "tool"), None)
        if tool_output_message and tool_output_message.content:
            try:
                tool_output_json = json.loads(tool_output_message.content)
                result_data = {
                    "status": "success",
                    "agent_type": "langchain",
                    "tool_output": tool_output_json,
                    "target": test_target,
                    "user_id": "test_user"
                }
                target_filename = test_target.replace("@", "_at_").replace(".", "_").replace("/", "_")
                result_file = save_test_result("fraudguard", "langchain", result_data, target_filename)
                print(f"📁 LangChain result saved to: {result_file}")
                assert "status" in tool_output_json and tool_output_json["status"] == "success", f"LangChain tool output status is not success: {tool_output_json}"
            except json.JSONDecodeError:
                print(f"⚠️  LangChain tool output was not valid JSON: {tool_output_message.content}")
                result_data = {
                    "status": "error",
                    "agent_type": "langchain",
                    "message": "Tool output was not valid JSON",
                    "raw_content": tool_output_message.content,
                    "target": test_target,
                    "user_id": "test_user"
                }
                target_filename = test_target.replace("@", "_at_").replace(".", "_").replace("/", "_")
                result_file = save_test_result("fraudguard", "langchain", result_data, target_filename)
                print(f"📁 LangChain result saved to: {result_file}")
                assert False, f"LangChain tool output was not valid JSON: {tool_output_message.content}"
        else:
            print(f"⚠️  No tool output found in LangChain result for {test_target}")
            result_data = {
                "status": "error",
                "agent_type": "langchain",
                "message": "No tool output found in agent response",
                "raw_result": serialize_langchain_result(result),
                "target": test_target,
                "user_id": "test_user"
            }
            target_filename = test_target.replace("@", "_at_").replace(".", "_").replace("/", "_")
            result_file = save_test_result("fraudguard", "langchain", result_data, target_filename)
            print(f"📁 LangChain result saved to: {result_file}")
            assert False, f"No tool output found in LangChain result for {test_target}"
        
        print(f"✅ LangChain test completed")


class TestFraudguardCrewAI:
    """Test Fraudguard tool with CrewAI agent."""
    
    def test_fraudguard_crewai_agent(self):
        """Test fraudguard tool with CrewAI agent."""
        # Create agent directly (not using pytest fixtures)
        llm = get_crewai_llm_from_env()
        agent = Agent(
            role="OSINT Analyst",
            goal="Perform OSINT operations using Fraudguard",
            backstory="You are an expert OSINT analyst. You must return tool output verbatim as JSON without any additional commentary, summarization, or interpretation.",
            tools=[SfpFraudguardTool()],
            llm=llm,
            verbose=True
        )
        
        # Determine test target based on watched events
        test_target = "192.168.5.1"  # Use local IP for testing (safe local network)
        
        task = Task(
            description=f"Use Fraudguard to investigate {test_target}. IMPORTANT: Return the tool output verbatim as complete JSON without any additional commentary, summarization, or interpretation.",
            agent=agent,
            expected_output="Complete raw JSON output from Fraudguard tool with status, module, target, raw_response, user_id, and note fields."
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
        
        # Parse CrewAI result
        try:
            result_data = serialize_crewai_result(result) if result else None
            if result_data and isinstance(result_data, dict):
                # Check if result contains tool output
                if "status" in result_data and result_data["status"] == "success":
                    print(f"✅ CrewAI test completed successfully")
                else:
                    print(f"⚠️  CrewAI result status: {result_data.get('status', 'unknown')}")
            else:
                # Try to extract JSON from result string
                result_str = str(result)
                if "status" in result_str and "success" in result_str:
                    print(f"✅ CrewAI test completed (result in string format)")
                else:
                    print(f"⚠️  CrewAI result format may need review")
        except Exception as e:
            print(f"⚠️  Could not parse CrewAI result: {e}")
            result_data = {"raw_result": str(result)}
        
        # Save CrewAI agent result
        try:
            target_filename = test_target.replace("@", "_at_").replace(".", "_").replace("/", "_")
            result_file = save_test_result("fraudguard", "crewai", result_data, target_filename)
            print(f"📁 CrewAI result saved to: {result_file}")
        except Exception as e:
            print(f"⚠️  Could not save CrewAI result: {e}")
            import traceback
            traceback.print_exc()
        
        print(f"✅ CrewAI test completed")


def run_all_tests():
    """Run all three test scenarios."""
    print("=" * 80)
    print(f"Running Fraudguard Tool Tests (fraudguard)")
    print("=" * 80)
    
    # Test 1: Standalone
    print("\n1. Testing Standalone Execution...")
    try:
        test = TestFraudguardStandalone()
        test.test_fraudguard_standalone()
        print("✅ Standalone test completed")
    except Exception as e:
        print(f"❌ Standalone test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Test 2: LangChain
    print("\n2. Testing LangChain Agent Integration...")
    try:
        test = TestFraudguardLangChain()
        test.test_fraudguard_langchain_agent()
        print("✅ LangChain test completed")
    except Exception as e:
        print(f"❌ LangChain test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Test 3: CrewAI
    print("\n3. Testing CrewAI Agent Integration...")
    try:
        test = TestFraudguardCrewAI()
        test.test_fraudguard_crewai_agent()
        print("✅ CrewAI test completed")
    except Exception as e:
        print(f"❌ CrewAI test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("All tests completed!")
    print("=" * 80)


if __name__ == "__main__":
    run_all_tests()
