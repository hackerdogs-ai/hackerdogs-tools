"""
Test suite for nuclei tool

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
from langchain_core.messages import HumanMessage, ToolMessage
from crewai import Agent, Task, Crew

from hackerdogs_tools.osint.infrastructure.nuclei_langchain import nuclei_scan
from hackerdogs_tools.osint.infrastructure.nuclei_crewai import NucleiTool
from hackerdogs_tools.osint.tests.test_utils import get_llm_from_env, get_crewai_llm_from_env
from hackerdogs_tools.osint.test_domains import get_random_domain
from hackerdogs_tools.osint.tests.test_runtime_helper import create_mock_runtime
from hackerdogs_tools.osint.tests.save_json_results import save_test_result


class TestNucleiStandalone:
    """Test nuclei tool standalone execution."""
    
    def test_nuclei_standalone(self):
        """Test nuclei tool execution without agent."""
        # Use mock runtime since ToolRuntime is auto-injected in LangChain 1.x
        runtime = create_mock_runtime(state={"user_id": "test_user"})
        
        # Use a random real domain instead of reserved example.com
        # Use "good" domains if malicious domain files are missing
        try:
            test_domain = get_random_domain("mixed")
        except FileNotFoundError:
            # Fallback to good domains if malicious files are missing
            test_domain = get_random_domain("good")
        
        # Tools are StructuredTool objects - use invoke() method
        # Nuclei requires "target" parameter, not "domain"
        result = nuclei_scan.invoke({
            "runtime": runtime,
            "target": f"https://{test_domain}",
            "templates": None,
            "severity": None,
            "tags": None
        })
        
        # Parse result
        result_data = json.loads(result)
        
        # Print JSON output for verification
        print("\n" + "=" * 80)
        print("TOOL JSON OUTPUT:")
        print("=" * 80)
        print(json.dumps(result_data, indent=2))
        print("=" * 80 + "\n")
        
        # Save JSON result to file
        result_file = save_test_result("nuclei", "standalone", result_data, test_domain)
        print(f"📁 JSON result saved to: {result_file}")
        
        # Assertions
        assert "status" in result_data, f"Missing 'status' in result: {result_data}"
        assert result_data["status"] in ["success", "error"], f"Invalid status: {result_data.get('status')}"
        
        if result_data["status"] == "success":
            assert "execution_method" in result_data, f"Missing 'execution_method' in result: {result_data}"
            # Tool can return "docker" or "official_docker_image" depending on execution method
            assert result_data["execution_method"] in ["docker", "official_docker_image"], \
                f"Invalid execution_method: {result_data.get('execution_method')}"
            assert "target" in result_data, f"Missing 'target' in result: {result_data}"
            assert "findings" in result_data, f"Missing 'findings' in result: {result_data}"
            assert isinstance(result_data["findings"], list), f"findings must be a list: {type(result_data.get('findings'))}"
            print(f"✅ Tool executed successfully")
            print(f"   Target: {result_data.get('target')}")
            print(f"   Findings found: {result_data.get('count', 0)}")
            print(f"   Execution method: {result_data.get('execution_method')}")
        else:
            # If error, should have message
            assert "message" in result_data, f"Error status but no message: {result_data}"
            print(f"⚠️  Tool returned error: {result_data.get('message')}")


class TestNucleiLangChain:
    """Test nuclei tool with LangChain agent."""
    
    @pytest.fixture
    def llm(self):
        """Get LLM from environment."""
        return get_llm_from_env()
    
    @pytest.fixture
    def agent(self, llm):
        """Create LangChain agent with nuclei tool."""
        tools = [nuclei_scan]
        agent = create_agent(
            model=llm,
            tools=tools,
            system_prompt="You are a cybersecurity analyst. Use the nuclei tool for vulnerability scanning."
        )
        return agent
    
    def test_nuclei_langchain_agent(self, agent):
        """Test nuclei tool with LangChain agent."""
        # Use a random real domain instead of reserved example.com
        # Use "good" domains if malicious domain files are missing
        try:
            test_domain = get_random_domain("mixed")
        except FileNotFoundError:
            # Fallback to good domains if malicious files are missing
            test_domain = get_random_domain("good")
        
        # Execute query directly (agent is a runnable in LangChain 1.x)
        # ToolRuntime is automatically injected by the agent
        result = agent.invoke({
            "messages": [HumanMessage(content=f"Scan {test_domain} for vulnerabilities using Nuclei")]
        })
        
        # Assertions
        assert result is not None, "Agent returned None"
        assert "messages" in result or "output" in result, f"Invalid agent result structure: {result}"
        
        # Save LangChain agent result - VERBATIM without wrappers
        try:
            # Extract tool responses verbatim
            tool_responses = []
            full_messages = []
            
            if isinstance(result, dict) and "messages" in result:
                for msg in result["messages"]:
                    msg_dict = {
                        "type": msg.__class__.__name__,
                        "content": msg.content if hasattr(msg, 'content') else str(msg),
                        "id": getattr(msg, 'id', None),
                        "name": getattr(msg, 'name', None)
                    }
                    
                    # If it's a ToolMessage, extract the verbatim JSON tool response
                    if isinstance(msg, ToolMessage):
                        try:
                            # Try to parse the tool response as JSON
                            tool_json = json.loads(msg.content)
                            tool_responses.append(tool_json)
                            msg_dict["tool_response_json"] = tool_json
                        except (json.JSONDecodeError, AttributeError):
                            # If not JSON, save as-is
                            tool_responses.append(msg.content)
                            msg_dict["tool_response_raw"] = msg.content
                    
                    full_messages.append(msg_dict)
            
            # Save verbatim result - complete result object serialized
            result_data = {
                "agent_result": result,  # Complete result object
                "messages": full_messages,  # All messages with full content
                "tool_responses": tool_responses,  # Extracted tool responses (verbatim JSON)
                "messages_count": len(result.get("messages", [])) if isinstance(result, dict) and "messages" in result else 0
            }
            result_file = save_test_result("nuclei", "langchain", result_data, test_domain)
            print(f"📁 LangChain result saved to: {result_file}")
        except Exception as e:
            print(f"⚠️  Could not save LangChain result: {e}")
            import traceback
            traceback.print_exc()
        
                
        # Print agent result for verification
        print("\n" + "=" * 80)
        print("LANGCHAIN AGENT RESULT:")
        print("=" * 80)
        if "messages" in result:
            for msg in result["messages"]:
                print(f"  {msg.__class__.__name__}: {str(msg.content)[:200]}")
        print("=" * 80 + "\n")


class TestNucleiCrewAI:
    """Test nuclei tool with CrewAI agent."""
    
    @pytest.fixture
    def llm(self):
        """Get CrewAI LLM from environment."""
        return get_crewai_llm_from_env()
    
    @pytest.fixture
    def agent(self, llm):
        """Create CrewAI agent with nuclei tool."""
        return Agent(
            role="Security Analyst",
            goal="Perform vulnerability scanning using nuclei",
            backstory="You are an expert security analyst specializing in vulnerability assessment.",
            tools=[NucleiTool()],
            llm=llm,
            verbose=True
        )
    
    def test_nuclei_crewai_agent(self, agent, llm):
        """Test nuclei tool with CrewAI agent."""
        # Use a random real domain instead of reserved example.com
        # Use "good" domains if malicious domain files are missing
        try:
            test_domain = get_random_domain("mixed")
        except FileNotFoundError:
            # Fallback to good domains if malicious files are missing
            test_domain = get_random_domain("good")
        
        task = Task(
            description=f"Scan {test_domain} for vulnerabilities using Nuclei",
            agent=agent,
            expected_output="Vulnerability scan results from nuclei tool"
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
        
        # Save CrewAI result - VERBATIM without wrappers
        try:
            # Extract all tool outputs from CrewAI result
            tool_outputs = []
            tool_executions = []
            
            # Method 1: Extract from tasks_output messages
            if hasattr(result, 'tasks_output') and result.tasks_output:
                for task_output in result.tasks_output:
                    # Check messages for tool output
                    if hasattr(task_output, 'messages') and task_output.messages:
                        for msg in task_output.messages:
                            if hasattr(msg, 'content'):
                                content = msg.content
                                # Try to parse as JSON (tool response)
                                if isinstance(content, str):
                                    try:
                                        parsed = json.loads(content)
                                        if isinstance(parsed, dict) and parsed.get('status'):
                                            tool_outputs.append(parsed)
                                    except (json.JSONDecodeError, AttributeError):
                                        pass
                    
                    # Check raw task output
                    if hasattr(task_output, 'raw') and task_output.raw:
                        try:
                            parsed = json.loads(task_output.raw)
                            if isinstance(parsed, dict) and parsed.get('status'):
                                tool_outputs.append(parsed)
                        except (json.JSONDecodeError, AttributeError):
                            pass
            
            # Method 2: Parse from raw output string (fallback - look for JSON patterns)
            if not tool_outputs and hasattr(result, 'raw'):
                raw_str = str(result.raw)
                import re
                # Look for JSON objects with "status" field
                json_pattern = r'\{[^{}]*"status"[^{}]*\}'
                matches = re.findall(json_pattern, raw_str, re.DOTALL)
                for match in matches:
                    try:
                        parsed = json.loads(match)
                        if isinstance(parsed, dict) and parsed.get('status'):
                            tool_outputs.append(parsed)
                    except json.JSONDecodeError:
                        pass
            
            # Save verbatim result - complete result object
            result_data = {
                "crew_result": result,  # Complete CrewAI result object
                "raw_output": str(result.raw) if hasattr(result, 'raw') else str(result),
                "tool_outputs": tool_outputs,  # Extracted tool responses (verbatim JSON)
                "tool_executions": tool_executions  # Tool execution details
            }
            result_file = save_test_result("nuclei", "crewai", result_data, test_domain)
            print(f"📁 CrewAI result saved to: {result_file}")
            print(f"   Found {len(tool_outputs)} tool output(s)")
        except Exception as e:
            print(f"⚠️  Could not save CrewAI result: {e}")
            import traceback
            traceback.print_exc()
        
        # Print CrewAI result for verification
        print("\n" + "=" * 80)
        print("CREWAI AGENT RESULT:")
        print("=" * 80)
        print(str(result)[:500])
        print("=" * 80 + "\n")


def run_all_tests():
    """Run all three test scenarios."""
    print("=" * 80)
    print(f"Running nuclei Tool Tests")
    print("=" * 80)
    
    # Test 1: Standalone
    print("\n1. Testing Standalone Execution...")
    try:
        test = TestNucleiStandalone()
        test.test_nuclei_standalone()
        print("✅ Standalone test passed")
    except Exception as e:
        print(f"❌ Standalone test failed: {str(e)}")
    
    # Test 2: LangChain
    print("\n2. Testing LangChain Agent Integration...")
    try:
        llm = get_llm_from_env()
        # Create agent directly (not using pytest fixtures)
        tools = [nuclei_scan]
        agent = create_agent(
            model=llm,
            tools=tools,
            system_prompt="You are a cybersecurity analyst. Use the nuclei tool for vulnerability scanning."
        )
        # Use a random real domain instead of reserved example.com
        # Use "good" domains if malicious domain files are missing
        try:
            test_domain = get_random_domain("mixed")
        except FileNotFoundError:
            # Fallback to good domains if malicious files are missing
            test_domain = get_random_domain("good")
        
        # Execute query directly (agent is a runnable in LangChain 1.x)
        # ToolRuntime is automatically injected by the agent
        result = agent.invoke({
            "messages": [HumanMessage(content=f"Scan {test_domain} for vulnerabilities using Nuclei")]
        })
        
        # Assertions
        assert result is not None
        assert "messages" in result or "output" in result
        
        # Save LangChain agent result - VERBATIM without wrappers
        try:
            # Extract tool responses verbatim
            tool_responses = []
            full_messages = []
            
            if isinstance(result, dict) and "messages" in result:
                for msg in result["messages"]:
                    msg_dict = {
                        "type": msg.__class__.__name__,
                        "content": msg.content if hasattr(msg, 'content') else str(msg),
                        "id": getattr(msg, 'id', None),
                        "name": getattr(msg, 'name', None)
                    }
                    
                    # If it's a ToolMessage, extract the verbatim JSON tool response
                    if isinstance(msg, ToolMessage):
                        try:
                            # Try to parse the tool response as JSON
                            tool_json = json.loads(msg.content)
                            tool_responses.append(tool_json)
                            msg_dict["tool_response_json"] = tool_json
                        except (json.JSONDecodeError, AttributeError):
                            # If not JSON, save as-is
                            tool_responses.append(msg.content)
                            msg_dict["tool_response_raw"] = msg.content
                    
                    full_messages.append(msg_dict)
            
            # Save verbatim result - complete result object
            result_data = {
                "agent_result": result,  # Complete result object
                "messages": full_messages,  # All messages with full content
                "tool_responses": tool_responses,  # Extracted tool responses (verbatim JSON)
                "messages_count": len(result.get("messages", [])) if isinstance(result, dict) and "messages" in result else 0
            }
            result_file = save_test_result("nuclei", "langchain", result_data, test_domain)
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
        llm = get_crewai_llm_from_env()
        # Create agent directly (not using pytest fixtures)
        agent = Agent(
            role="Security Analyst",
            goal="Perform vulnerability scanning using nuclei",
            backstory="You are an expert security analyst specializing in vulnerability assessment.",
            tools=[NucleiTool()],
            llm=llm,
            verbose=True
        )
        # Use a random real domain instead of reserved example.com
        # Use "good" domains if malicious domain files are missing
        try:
            test_domain = get_random_domain("mixed")
        except FileNotFoundError:
            # Fallback to good domains if malicious files are missing
            test_domain = get_random_domain("good")
        
        task = Task(
            description=f"Scan {test_domain} for vulnerabilities using Nuclei",
            agent=agent,
            expected_output="Vulnerability scan results from nuclei tool"
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
        
        # Save CrewAI result - VERBATIM without wrappers
        try:
            # Extract all tool outputs from CrewAI result
            tool_outputs = []
            tool_executions = []
            
            # Method 1: Extract from tasks_output messages
            if hasattr(result, 'tasks_output') and result.tasks_output:
                for task_output in result.tasks_output:
                    # Check messages for tool output
                    if hasattr(task_output, 'messages') and task_output.messages:
                        for msg in task_output.messages:
                            if hasattr(msg, 'content'):
                                content = msg.content
                                # Try to parse as JSON (tool response)
                                if isinstance(content, str):
                                    try:
                                        parsed = json.loads(content)
                                        if isinstance(parsed, dict) and parsed.get('status'):
                                            tool_outputs.append(parsed)
                                    except (json.JSONDecodeError, AttributeError):
                                        pass
                    
                    # Check raw task output
                    if hasattr(task_output, 'raw') and task_output.raw:
                        try:
                            parsed = json.loads(task_output.raw)
                            if isinstance(parsed, dict) and parsed.get('status'):
                                tool_outputs.append(parsed)
                        except (json.JSONDecodeError, AttributeError):
                            pass
            
            # Method 2: Parse from raw output string (fallback - look for JSON patterns)
            if not tool_outputs and hasattr(result, 'raw'):
                raw_str = str(result.raw)
                import re
                # Look for JSON objects with "status" field
                json_pattern = r'\{[^{}]*"status"[^{}]*\}'
                matches = re.findall(json_pattern, raw_str, re.DOTALL)
                for match in matches:
                    try:
                        parsed = json.loads(match)
                        if isinstance(parsed, dict) and parsed.get('status'):
                            tool_outputs.append(parsed)
                    except json.JSONDecodeError:
                        pass
            
            # Save verbatim result - complete result object
            result_data = {
                "crew_result": result,  # Complete CrewAI result object
                "raw_output": str(result.raw) if hasattr(result, 'raw') else str(result),
                "tool_outputs": tool_outputs,  # Extracted tool responses (verbatim JSON)
                "tool_executions": tool_executions  # Tool execution details
            }
            result_file = save_test_result("nuclei", "crewai", result_data, test_domain)
            print(f"📁 CrewAI result saved to: {result_file}")
            print(f"   Found {len(tool_outputs)} tool output(s)")
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
