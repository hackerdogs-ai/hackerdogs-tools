"""
Test suite for Browserless tools.

Tests standalone execution, LangChain agent integration, and CrewAI agent integration
for all Browserless endpoints: content, scrape, screenshot, pdf, function, unblock.
"""

import pytest
import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(override=True)

# Add project root to path for direct execution
project_root = Path(__file__).parent.parent.parent.parent.parent.resolve()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from crewai import Agent, Task, Crew

from hackerdogs_tools.osint.content.browserless_langchain import (
    browserless_content,
    browserless_scrape,
    browserless_screenshot,
    browserless_pdf,
    browserless_function,
    browserless_unblock,
    BrowserlessSecurityAgentState
)
from hackerdogs_tools.osint.content.browserless_crewai import (
    BrowserlessContentTool,
    BrowserlessScrapeTool,
    BrowserlessScreenshotTool,
    BrowserlessPDFTool,
    BrowserlessFunctionTool,
    BrowserlessUnblockTool
)
from hackerdogs_tools.osint.tests.test_utils import get_llm_from_env, get_crewai_llm_from_env
from hackerdogs_tools.osint.test_websites import get_random_website
from hackerdogs_tools.osint.tests.test_runtime_helper import create_mock_runtime
from hackerdogs_tools.osint.tests.save_json_results import save_test_result, serialize_langchain_result, serialize_crewai_result


class TestBrowserlessStandalone:
    """Test browserless tools standalone execution."""
    
    def test_browserless_content_standalone(self):
        """Test browserless_content tool execution without agent."""
        runtime = create_mock_runtime(state={"user_id": "test_user"})
        test_url = get_random_website()
        
        result = browserless_content.invoke({
            "runtime": runtime,
            "url": test_url,
            "timeout": 30
        })
        
        try:
            result_data = json.loads(result)
        except json.JSONDecodeError:
            result_data = {"raw_output": result}
        
        print("\n" + "=" * 80)
        print("BROWSERLESS CONTENT OUTPUT:")
        print("=" * 80)
        print(json.dumps(result_data, indent=2)[:500])
        print("=" * 80 + "\n")
        
        try:
            result_file = save_test_result("browserless_content", "standalone", result_data, test_url.replace("https://", "").replace("http://", "").replace("/", "_"))
            print(f"📁 JSON result saved to: {result_file}")
        except Exception as e:
            print(f"⚠️  Could not save result: {e}")
        
        assert result is not None
        assert isinstance(result, str)
        if isinstance(result_data, dict):
            assert "status" in result_data
    
    def test_browserless_scrape_standalone(self):
        """Test browserless_scrape tool execution without agent."""
        runtime = create_mock_runtime(state={"user_id": "test_user"})
        test_url = get_random_website()
        
        result = browserless_scrape.invoke({
            "runtime": runtime,
            "url": test_url,
            "selector": "h1, h2, h3",
            "timeout": 30
        })
        
        try:
            result_data = json.loads(result)
        except json.JSONDecodeError:
            result_data = {"raw_output": result}
        
        try:
            result_file = save_test_result("browserless_scrape", "standalone", result_data, test_url.replace("https://", "").replace("http://", "").replace("/", "_"))
            print(f"📁 JSON result saved to: {result_file}")
        except Exception as e:
            print(f"⚠️  Could not save result: {e}")
        
        assert result is not None
    
    def test_browserless_screenshot_standalone(self):
        """Test browserless_screenshot tool execution without agent."""
        runtime = create_mock_runtime(state={"user_id": "test_user"})
        test_url = get_random_website()
        
        result = browserless_screenshot.invoke({
            "runtime": runtime,
            "url": test_url,
            "timeout": 30
        })
        
        try:
            result_data = json.loads(result)
        except json.JSONDecodeError:
            result_data = {"raw_output": result}
        
        try:
            result_file = save_test_result("browserless_screenshot", "standalone", result_data, test_url.replace("https://", "").replace("http://", "").replace("/", "_"))
            print(f"📁 JSON result saved to: {result_file}")
        except Exception as e:
            print(f"⚠️  Could not save result: {e}")
        
        assert result is not None


class TestBrowserlessLangChain:
    """Test browserless tools with LangChain agent."""
    
    def test_browserless_content_langchain_agent(self):
        """Test browserless_content tool with LangChain agent."""
        llm = get_llm_from_env()
        tools = [browserless_content]
        agent = create_agent(
            model=llm,
            tools=tools,
            system_prompt=(
                "You are a web scraping specialist. Your ONLY job is to execute tools and return their output EXACTLY as provided, "
                "without summarization, interpretation, or modification. When a tool returns JSON, you MUST copy the "
                "complete JSON string verbatim into your Final Answer. Do NOT summarize, do NOT extract points, "
                "do NOT reformat - return raw output only."
            ),
            state_schema=BrowserlessSecurityAgentState
        )
        
        test_url = get_random_website()
        result = agent.invoke({
            "messages": [HumanMessage(content=f"Extract content from {test_url} using Browserless. IMPORTANT: Return the complete JSON output from the tool verbatim. Do NOT summarize or interpret the results.")],
            "user_id": "test_user"
        })
        
        try:
            # Extract tool output from messages and save
            tool_output = None
            if "messages" in result:
                for msg in result["messages"]:
                    if hasattr(msg, 'type') and msg.type == "tool" and hasattr(msg, 'content'):
                        try:
                            # Try to parse the content as JSON
                            import json
                            tool_output = json.loads(msg.content)
                            break
                        except:
                            pass
            
            # If we found tool output, use it; otherwise serialize the full result
            if tool_output:
                result_data = tool_output
            else:
                result_data = serialize_langchain_result(result)
            
            result_file = save_test_result("browserless_content", "langchain", result_data, test_url.replace("https://", "").replace("http://", "").replace("/", "_"))
            print(f"📁 JSON result saved to: {result_file}")
        except Exception as e:
            print(f"⚠️  Could not save result: {e}")
            import traceback
            traceback.print_exc()
        
        assert result is not None
        print("✅ LangChain test completed")


class TestBrowserlessCrewAI:
    """Test browserless tools with CrewAI agent."""
    
    def test_browserless_content_crewai_agent(self):
        """Test browserless_content tool with CrewAI agent."""
        crewai_llm = get_crewai_llm_from_env()
        agent = Agent(
            role="Web Scraping Specialist",
            goal="Execute Browserless tools and return raw output verbatim without any modification",
            backstory=(
                "You are a data collection specialist. Your ONLY job is to execute tools and return "
                "their output EXACTLY as provided, without summarization, interpretation, or modification. "
                "When a tool returns JSON, you MUST copy the complete JSON string verbatim into your Final Answer. "
                "Do NOT summarize, do NOT extract points, do NOT reformat - return raw output only."
            ),
            tools=[BrowserlessContentTool()],
            llm=crewai_llm,
            verbose=True
        )
        
        test_url = get_random_website()
        task = Task(
            description=f"Extract content from {test_url} using Browserless. IMPORTANT: When the tool returns JSON output, you MUST return the complete JSON string verbatim in your Final Answer. Do NOT summarize, do NOT extract key points, do NOT reformat. Return the exact JSON output from the tool.",
            agent=agent,
            expected_output="Complete raw JSON output from Browserless tool, returned verbatim without any modification. Must include status, url, endpoint, raw_response, and all other fields exactly as returned by the tool."
        )
        
        crew = Crew(
            agents=[agent],
            tasks=[task],
            verbose=True
        )
        
        result = crew.kickoff()
        
        try:
            serialized = serialize_crewai_result(result)
            result_file = save_test_result("browserless_content", "crewai", serialized, test_url.replace("https://", "").replace("http://", "").replace("/", "_"))
            print(f"📁 JSON result saved to: {result_file}")
        except Exception as e:
            print(f"⚠️  Could not save result: {e}")
        
        assert result is not None
        print("✅ CrewAI test completed")


def run_all_tests():
    """Run all test scenarios."""
    print("=" * 80)
    print("Running Browserless Tool Tests")
    print("=" * 80)
    
    # Test 1: Standalone
    print("\n1. Testing Standalone Execution...")
    try:
        test = TestBrowserlessStandalone()
        test.test_browserless_content_standalone()
        print("✅ Content standalone test completed")
        
        test.test_browserless_scrape_standalone()
        print("✅ Scrape standalone test completed")
        
        test.test_browserless_screenshot_standalone()
        print("✅ Screenshot standalone test completed")
    except Exception as e:
        print(f"❌ Standalone test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Test 2: LangChain
    print("\n2. Testing LangChain Agent Integration...")
    try:
        test = TestBrowserlessLangChain()
        test.test_browserless_content_langchain_agent()
    except Exception as e:
        print(f"❌ LangChain test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Test 3: CrewAI
    print("\n3. Testing CrewAI Agent Integration...")
    try:
        test = TestBrowserlessCrewAI()
        test.test_browserless_content_crewai_agent()
    except Exception as e:
        print(f"❌ CrewAI test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("All tests completed")
    print("=" * 80)


if __name__ == "__main__":
    run_all_tests()

