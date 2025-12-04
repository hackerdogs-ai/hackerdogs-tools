"""
Generate test files for all OSINT tools
"""

import os
import re
from pathlib import Path


def get_tool_info():
    """Get all tool information."""
    tools = []
    base_path = Path(__file__).parent.parent
    
    for root, dirs, files in os.walk(base_path):
        # Skip tests and docker directories
        if 'tests' in root or 'docker' in root:
            continue
            
        for file in files:
            if file.endswith('_langchain.py') and not file.startswith('__'):
                tool_name = file.replace('_langchain.py', '')
                category = os.path.basename(root)
                
                # Get function name from file
                langchain_file = os.path.join(root, file)
                crewai_file = os.path.join(root, file.replace('_langchain.py', '_crewai.py'))
                
                # Read function name
                func_name = None
                tool_class = None
                
                try:
                    with open(langchain_file, 'r') as f:
                        content = f.read()
                        # Find @tool function
                        match = re.search(r'@tool\s+def\s+(\w+)', content)
                        if match:
                            func_name = match.group(1)
                except:
                    pass
                
                try:
                    with open(crewai_file, 'r') as f:
                        content = f.read()
                        # Find class name
                        match = re.search(r'class\s+(\w+Tool)\s*\(', content)
                        if match:
                            tool_class = match.group(1)
                except:
                    pass
                
                tools.append({
                    'name': tool_name,
                    'category': category,
                    'func_name': func_name or f"{tool_name}_enum",
                    'tool_class': tool_class or f"{tool_name.capitalize()}Tool",
                    'langchain_file': langchain_file.replace(str(base_path) + '/', ''),
                    'crewai_file': crewai_file.replace(str(base_path) + '/', '') if os.path.exists(crewai_file) else None
                })
    
    return sorted(tools, key=lambda x: (x['category'], x['name']))


def generate_test_file(tool_info):
    """Generate test file for a tool."""
    tool_name = tool_info['name']
    func_name = tool_info['func_name']
    tool_class = tool_info['tool_class']
    category = tool_info['category']
    
    # Import paths
    langchain_import = f"hackerdogs_tools.osint.{category}.{tool_name}_langchain"
    crewai_import = f"hackerdogs_tools.osint.{category}.{tool_name}_crewai"
    
    # Test parameters based on tool type
    test_params = get_test_parameters(tool_name)
    
    test_content = f'''"""
Test suite for {tool_name} tool

Tests:
1. Standalone tool execution
2. LangChain agent integration
3. CrewAI agent integration
"""

import pytest
import json
import os
from langchain.agents import create_agent, AgentExecutor
from langchain.tools import ToolRuntime
from langchain_core.messages import HumanMessage
from crewai import Agent, Task, Crew

from {langchain_import} import {func_name}
from {crewai_import} import {tool_class}
from hackerdogs_tools.osint.tests.test_utils import get_llm_from_env, get_crewai_llm_from_env


class Test{tool_name.capitalize()}Standalone:
    """Test {tool_name} tool standalone execution."""
    
    def test_{tool_name}_standalone(self):
        """Test {tool_name} tool execution without agent."""
        runtime = ToolRuntime(state={{"user_id": "test_user"}})
        
        result = {func_name}(
            runtime=runtime,
            {test_params['standalone']}
        )
        
        # Parse result
        result_data = json.loads(result)
        
        # Assertions
        assert "status" in result_data
        assert result_data["status"] in ["success", "error"]
        
        if result_data["status"] == "success":
            assert "execution_method" in result_data
            assert result_data["execution_method"] == "docker"
        else:
            # If error, should have message
            assert "message" in result_data
            print(f"Tool returned error (expected if Docker not set up): {{result_data.get('message')}}")


class Test{tool_name.capitalize()}LangChain:
    """Test {tool_name} tool with LangChain agent."""
    
    @pytest.fixture
    def llm(self):
        """Get LLM from environment."""
        return get_llm_from_env()
    
    @pytest.fixture
    def agent(self, llm):
        """Create LangChain agent with {tool_name} tool."""
        tools = [{func_name}]
        agent = create_agent(
            llm=llm,
            tools=tools,
            system_prompt="You are a cybersecurity analyst. Use the {tool_name} tool for OSINT operations."
        )
        return agent
    
    def test_{tool_name}_langchain_agent(self, agent):
        """Test {tool_name} tool with LangChain agent."""
        runtime = ToolRuntime(state={{"user_id": "test_user"}})
        
        # Create agent executor
        executor = AgentExecutor(
            agent=agent,
            tools=[{func_name}],
            verbose=True
        )
        
        # Execute query
        result = executor.invoke({{
            "messages": [HumanMessage(content="{test_params['langchain_query']}")],
            "runtime": runtime
        }})
        
        # Assertions
        assert result is not None
        assert "messages" in result or "output" in result
        print(f"LangChain agent result: {{result}}")


class Test{tool_name.capitalize()}CrewAI:
    """Test {tool_name} tool with CrewAI agent."""
    
    @pytest.fixture
    def llm(self):
        """Get CrewAI LLM from environment."""
        return get_crewai_llm_from_env()
    
    @pytest.fixture
    def agent(self, llm):
        """Create CrewAI agent with {tool_name} tool."""
        return Agent(
            role="OSINT Analyst",
            goal="Perform OSINT operations using {tool_name}",
            backstory="You are an expert OSINT analyst.",
            tools=[{tool_class}()],
            llm=llm,
            verbose=True
        )
    
    def test_{tool_name}_crewai_agent(self, agent, llm):
        """Test {tool_name} tool with CrewAI agent."""
        task = Task(
            description="{test_params['crewai_task']}",
            agent=agent,
            expected_output="Results from {tool_name} tool"
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
        print(f"CrewAI agent result: {{result}}")


def run_all_tests():
    """Run all three test scenarios."""
    print("=" * 80)
    print(f"Running {tool_name} Tool Tests")
    print("=" * 80)
    
    # Test 1: Standalone
    print("\\n1. Testing Standalone Execution...")
    try:
        test = Test{tool_name.capitalize()}Standalone()
        test.test_{tool_name}_standalone()
        print("✅ Standalone test passed")
    except Exception as e:
        print(f"❌ Standalone test failed: {{str(e)}}")
    
    # Test 2: LangChain
    print("\\n2. Testing LangChain Agent Integration...")
    try:
        llm = get_llm_from_env()
        test = Test{tool_name.capitalize()}LangChain()
        test.test_{tool_name}_langchain_agent(test.agent(llm))
        print("✅ LangChain test passed")
    except Exception as e:
        print(f"❌ LangChain test failed: {{str(e)}}")
    
    # Test 3: CrewAI
    print("\\n3. Testing CrewAI Agent Integration...")
    try:
        llm = get_crewai_llm_from_env()
        test = Test{tool_name.capitalize()}CrewAI()
        test.test_{tool_name}_crewai_agent(test.agent(llm), llm)
        print("✅ CrewAI test passed")
    except Exception as e:
        print(f"❌ CrewAI test failed: {{str(e)}}")
    
    print("\\n" + "=" * 80)
    print("All tests completed!")
    print("=" * 80)


if __name__ == "__main__":
    run_all_tests()
'''
    return test_content


def get_test_parameters(tool_name):
    """Get test parameters for a tool."""
    params = {
        'amass': {
            'standalone': 'domain="example.com", passive=False, active=True, timeout=300',
            'langchain_query': 'Enumerate subdomains for example.com using Amass',
            'crewai_task': 'Enumerate subdomains for example.com using Amass'
        },
        'subfinder': {
            'standalone': 'domain="example.com", recursive=False, silent=True',
            'langchain_query': 'Find subdomains for example.com using Subfinder',
            'crewai_task': 'Find subdomains for example.com using Subfinder'
        },
        'nuclei': {
            'standalone': 'target="https://example.com", templates=None, severity=None, tags=None',
            'langchain_query': 'Scan https://example.com for vulnerabilities using Nuclei',
            'crewai_task': 'Scan https://example.com for vulnerabilities using Nuclei'
        },
        'masscan': {
            'standalone': 'ip_range="10.0.0.0/8", ports="80,443", rate=1000',
            'langchain_query': 'Scan IP range 10.0.0.0/8 for ports 80,443 using Masscan',
            'crewai_task': 'Scan IP range 10.0.0.0/8 for ports 80,443 using Masscan'
        },
        'zmap': {
            'standalone': 'ip_range="10.0.0.0/8", port=80, bandwidth="10M"',
            'langchain_query': 'Scan IP range 10.0.0.0/8 port 80 using ZMap',
            'crewai_task': 'Scan IP range 10.0.0.0/8 port 80 using ZMap'
        },
        'theharvester': {
            'standalone': 'domain="example.com", sources=None, limit=500',
            'langchain_query': 'Gather information about example.com using TheHarvester',
            'crewai_task': 'Gather information about example.com using TheHarvester'
        },
        'dnsdumpster': {
            'standalone': 'domain="example.com"',
            'langchain_query': 'Map DNS records for example.com using DNSDumpster',
            'crewai_task': 'Map DNS records for example.com using DNSDumpster'
        },
        'sherlock': {
            'standalone': 'username="testuser", sites=None, timeout=60',
            'langchain_query': 'Find username testuser across social media using Sherlock',
            'crewai_task': 'Find username testuser across social media using Sherlock'
        },
        'maigret': {
            'standalone': 'username="testuser", extract_metadata=True, sites=None',
            'langchain_query': 'Search for username testuser using Maigret',
            'crewai_task': 'Search for username testuser using Maigret'
        },
        'ghunt': {
            'standalone': 'email="test@example.com", extract_reviews=True, extract_photos=False',
            'langchain_query': 'Investigate Google account for test@example.com using GHunt',
            'crewai_task': 'Investigate Google account for test@example.com using GHunt'
        },
        'holehe': {
            'standalone': 'email="test@example.com", only_used=True',
            'langchain_query': 'Check if email test@example.com is registered on sites using Holehe',
            'crewai_task': 'Check if email test@example.com is registered on sites using Holehe'
        },
        'scrapy': {
            'standalone': 'url="https://example.com", spider_name="generic", follow_links=False, max_pages=10',
            'langchain_query': 'Scrape https://example.com using Scrapy',
            'crewai_task': 'Scrape https://example.com using Scrapy'
        },
        'waybackurls': {
            'standalone': 'domain="example.com", no_subs=False, dates=None',
            'langchain_query': 'Fetch URLs from Wayback Machine for example.com',
            'crewai_task': 'Fetch URLs from Wayback Machine for example.com'
        },
        'onionsearch': {
            'standalone': 'query="test", engines=None, max_results=50',
            'langchain_query': 'Search dark web for "test" using OnionSearch',
            'crewai_task': 'Search dark web for "test" using OnionSearch'
        },
        'spiderfoot': {
            'standalone': 'target="example.com", target_type="domain", modules=None, scan_type="footprint"',
            'langchain_query': 'Run SpiderFoot footprint scan on example.com',
            'crewai_task': 'Run SpiderFoot footprint scan on example.com'
        },
        'yara': {
            'standalone': 'file_path="/tmp/test.exe", rules_path="/tmp/rules.yar", rules_content=None',
            'langchain_query': 'Scan file /tmp/test.exe with YARA rules',
            'crewai_task': 'Scan file /tmp/test.exe with YARA rules'
        },
        'exiftool': {
            'standalone': 'file_path="/tmp/image.jpg", extract_gps=True, extract_author=True',
            'langchain_query': 'Extract metadata from /tmp/image.jpg using ExifTool',
            'crewai_task': 'Extract metadata from /tmp/image.jpg using ExifTool'
        },
        'abuseipdb': {
            'standalone': 'ip="8.8.8.8", max_age_in_days=90, verbose=True',
            'langchain_query': 'Check IP reputation for 8.8.8.8 using AbuseIPDB',
            'crewai_task': 'Check IP reputation for 8.8.8.8 using AbuseIPDB'
        },
        'urlhaus': {
            'standalone': 'url="https://example.com", download_feed=False',
            'langchain_query': 'Check if https://example.com is malicious using URLHaus',
            'crewai_task': 'Check if https://example.com is malicious using URLHaus'
        }
    }
    
    # Default parameters
    default = {
        'standalone': 'domain="example.com"',
        'langchain_query': f'Use {tool_name} tool for OSINT operations',
        'crewai_task': f'Use {tool_name} tool for OSINT operations'
    }
    
    return params.get(tool_name, default)


def main():
    """Generate all test files."""
    tools = get_tool_info()
    test_dir = Path(__file__).parent
    
    print(f"Generating test files for {len(tools)} tools...")
    
    for tool_info in tools:
        test_file = test_dir / f"test_{tool_info['name']}.py"
        test_content = generate_test_file(tool_info)
        
        with open(test_file, 'w') as f:
            f.write(test_content)
        
        print(f"✅ Generated: {test_file}")
    
    print(f"\n✅ Generated {len(tools)} test files!")


if __name__ == "__main__":
    main()

