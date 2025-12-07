"""
Test suite for Crawl4AI tool.

Tests standalone execution, LangChain agent integration, and CrewAI agent integration.
"""

import pytest
import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add project root to path for direct execution
project_root = Path(__file__).parent.parent.parent.parent.parent.resolve()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from crewai import Agent, Task, Crew

from hackerdogs_tools.osint.content.crawl4ai_langchain import crawl4ai_crawl
from hackerdogs_tools.osint.content.crawl4ai_crewai import Crawl4AITool
from hackerdogs_tools.osint.tests.test_utils import get_llm_from_env, get_crewai_llm_from_env
from hackerdogs_tools.osint.test_websites import get_random_website
from hackerdogs_tools.osint.tests.test_runtime_helper import create_mock_runtime
from hackerdogs_tools.osint.tests.save_json_results import save_test_result, serialize_langchain_result, serialize_crewai_result


class TestCrawl4AIStandalone:
    """Test crawl4ai tool standalone execution."""
    
    def test_crawl4ai_standalone(self):
        """Test crawl4ai tool execution without agent."""
        # Use mock runtime since ToolRuntime is auto-injected in LangChain 1.x
        runtime = create_mock_runtime(state={"user_id": "test_user"})
        
        # Use a random website from the test websites list
        test_url = get_random_website()
        
        # Tools are StructuredTool objects - use invoke() method
        result = crawl4ai_crawl.invoke({
            "runtime": runtime,
            "url": test_url,
            "mode": "direct",
            "timeout": 30  # Reduced timeout for faster tests
        })
        
        # Crawl4AI returns JSON string
        try:
            result_data = json.loads(result)
        except json.JSONDecodeError:
            result_data = {"raw_output": result}
        
        # Print JSON output for verification
        print("\n" + "=" * 80)
        print("TOOL JSON OUTPUT:")
        print("=" * 80)
        print(json.dumps(result_data, indent=2))
        print("=" * 80 + "\n")
        
        # Save result
        try:
            result_file = save_test_result("crawl4ai", "standalone", result_data, test_url.replace("https://", "").replace("http://", "").replace("/", "_"))
            print(f"📁 JSON result saved to: {result_file}")
        except Exception as e:
            print(f"⚠️  Could not save result: {e}")
        
        # Basic assertions
        assert result is not None, "Result should not be None"
        assert isinstance(result, str), "Result should be a string"
        
        # Check if result contains expected structure
        if isinstance(result_data, dict):
            assert "status" in result_data, "Result should contain 'status' field"
            if result_data.get("status") == "success":
                assert "raw_response" in result_data, "Successful result should contain 'raw_response'"


class TestCrawl4AILangChain:
    """Test crawl4ai tool with LangChain agent."""
    
    @pytest.fixture
    def agent(self, llm):
        """Create LangChain agent with crawl4ai tool."""
        tools = [crawl4ai_crawl]
        agent = create_agent(
            model=llm,
            tools=tools,
            system_prompt="You are a web scraping specialist. Use the crawl4ai tool to crawl websites and extract content."
        )
        return agent
    
    @pytest.fixture
    def llm(self):
        """Get LLM from environment."""
        return get_llm_from_env()
    
    def test_crawl4ai_langchain_agent(self, agent, llm):
        """Test crawl4ai tool with LangChain agent."""
        # Use a random website from the test websites list
        test_url = get_random_website()
        
        # Execute query
        result = agent.invoke({
            "messages": [
                HumanMessage(content=f"Crawl the website {test_url} and extract the main content")
            ],
            "user_id": "test_user"
        })
        
        # Serialize and save result
        try:
            serialized = serialize_langchain_result(result)
            result_file = save_test_result("crawl4ai", "langchain", serialized, test_url.replace("https://", "").replace("http://", "").replace("/", "_"))
            print(f"📁 JSON result saved to: {result_file}")
        except Exception as e:
            print(f"⚠️  Could not save result: {e}")
        
        # Basic assertions
        assert result is not None, "Agent result should not be None"
        assert "messages" in result, "Result should contain 'messages'"


class TestCrawl4AICrewAI:
    """Test crawl4ai tool with CrewAI agent."""
    
    @pytest.fixture
    def agent(self, llm):
        """Create CrewAI agent with crawl4ai tool."""
        return Agent(
            role="Web Scraping Specialist",
            goal="Crawl websites and extract content using Crawl4AI",
            backstory="You are an expert at web scraping and content extraction.",
            tools=[Crawl4AITool()],
            llm=llm,
            verbose=True
        )
    
    @pytest.fixture
    def llm(self):
        """Get CrewAI LLM from environment."""
        return get_crewai_llm_from_env()
    
    def test_crawl4ai_crewai_agent(self, agent, llm):
        """Test crawl4ai tool with CrewAI agent."""
        # Use a random website from the test websites list
        test_url = get_random_website()
        
        # Create task
        task = Task(
            description=f"Crawl the website {test_url} and extract the main content",
            agent=agent,
            expected_output="JSON response with crawled content and extracted data"
        )
        
        # Create crew and execute
        crew = Crew(
            agents=[agent],
            tasks=[task],
            verbose=True
        )
        
        result = crew.kickoff()
        
        # Serialize and save result
        try:
            serialized = serialize_crewai_result(result)
            result_file = save_test_result("crawl4ai", "crewai", serialized, test_url.replace("https://", "").replace("http://", "").replace("/", "_"))
            print(f"📁 JSON result saved to: {result_file}")
        except Exception as e:
            print(f"⚠️  Could not save result: {e}")
        
        # Basic assertions
        assert result is not None, "Crew result should not be None"


def run_all_tests():
    """Run all crawl4ai tests."""
    print("=" * 80)
    print("Running Crawl4AI Tool Tests")
    print("=" * 80)
    
    # Standalone test
    print("\n1. Testing Standalone Execution...")
    try:
        test = TestCrawl4AIStandalone()
        test.test_crawl4ai_standalone()
        print("✅ Standalone test completed")
    except Exception as e:
        print(f"❌ Standalone test failed: {e}")
        import traceback
        traceback.print_exc()
    
    # LangChain test
    print("\n2. Testing LangChain Agent Integration...")
    try:
        llm = get_llm_from_env()
        tools = [crawl4ai_crawl]
        agent = create_agent(
            model=llm,
            tools=tools,
            system_prompt="You are a web scraping specialist. Use the crawl4ai tool to crawl websites and extract content."
        )
        
        test_url = get_random_website()
        result = agent.invoke({
            "messages": [
                HumanMessage(content=f"Crawl the website {test_url} and extract the main content")
            ],
            "user_id": "test_user"
        })
        
        # Serialize and save result
        try:
            serialized = serialize_langchain_result(result)
            result_file = save_test_result("crawl4ai", "langchain", serialized, test_url.replace("https://", "").replace("http://", "").replace("/", "_"))
            print(f"📁 JSON result saved to: {result_file}")
        except Exception as e:
            print(f"⚠️  Could not save result: {e}")
        
        print("✅ LangChain test completed")
    except Exception as e:
        print(f"❌ LangChain test failed: {e}")
        import traceback
        traceback.print_exc()
    
    # CrewAI test
    print("\n3. Testing CrewAI Agent Integration...")
    try:
        crewai_llm = get_crewai_llm_from_env()
        agent = Agent(
            role="Web Scraping Specialist",
            goal="Crawl websites and extract content using Crawl4AI",
            backstory="You are an expert at web scraping and content extraction.",
            tools=[Crawl4AITool()],
            llm=crewai_llm,
            verbose=True
        )
        
        test_url = get_random_website()
        task = Task(
            description=f"Crawl the website {test_url} and extract the main content",
            agent=agent,
            expected_output="JSON response with crawled content and extracted data"
        )
        
        crew = Crew(
            agents=[agent],
            tasks=[task],
            verbose=True
        )
        
        result = crew.kickoff()
        
        # Serialize and save result
        try:
            serialized = serialize_crewai_result(result)
            result_file = save_test_result("crawl4ai", "crewai", serialized, test_url.replace("https://", "").replace("http://", "").replace("/", "_"))
            print(f"📁 JSON result saved to: {result_file}")
        except Exception as e:
            print(f"⚠️  Could not save result: {e}")
        
        print("✅ CrewAI test completed")
    except Exception as e:
        print(f"❌ CrewAI test failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("All tests completed")
    print("=" * 80)


if __name__ == "__main__":
    run_all_tests()

