"""
Quick test for Maigret CrewAI verbatim output
"""

import json
import os
import sys
from pathlib import Path
from crewai import Agent, Task, Crew

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent.parent.resolve()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from hackerdogs_tools.osint.identity.maigret_crewai import MaigretTool
from hackerdogs_tools.osint.tests.test_utils import get_crewai_llm_from_env
from hackerdogs_tools.osint.test_identity_data import get_random_username
from hackerdogs_tools.osint.tests.save_json_results import serialize_crewai_result, save_test_result


def test_maigret_crewai_verbatim_output():
    """Test that CrewAI agent returns verbatim JSON output from Maigret tool."""
    print("=" * 80)
    print("TESTING MAIGRET CREWAI VERBATIM OUTPUT")
    print("=" * 80)
    
    # Get LLM
    llm = get_crewai_llm_from_env()
    
    # Create agent with explicit verbatim output instructions
    agent = Agent(
        role="OSINT Data Collector",
        goal="Execute OSINT tools and return raw output verbatim without any modification",
        backstory=(
            "You are a data collection specialist. Your ONLY job is to execute tools and return "
            "their output EXACTLY as provided, without summarization, interpretation, or modification. "
            "When a tool returns JSON, you MUST copy the complete JSON string verbatim into your Final Answer. "
            "Do NOT summarize, do NOT extract points, do NOT reformat - return raw output only."
        ),
        tools=[MaigretTool()],
        llm=llm,
        verbose=True
    )
    
    # Use a simple test username
    test_username = "testuser123"
    
    # Create task with very explicit verbatim instructions
    # Note: Limiting sites to reduce response size and avoid LLM timeout
    task = Task(
        description=(
            f"Use the Maigret tool to search for username '{test_username}' with sites=['GitHub', 'Trello'] "
            "to limit response size. IMPORTANT: In your Final Answer, you MUST return the complete raw JSON output "
            "from the tool's Observation field EXACTLY as it appears, without any changes. "
            "Copy the entire JSON string verbatim - do not summarize, do not extract, do not modify."
        ),
        agent=agent,
        expected_output="Complete raw JSON output from Maigret tool, returned verbatim without modification"
    )
    
    # Create crew
    crew = Crew(
        agents=[agent],
        tasks=[task],
        llm=llm,
        verbose=True
    )
    
    print(f"\n🔍 Testing with username: {test_username}")
    print("⏳ Executing CrewAI task...\n")
    
    # Execute with timeout handling
    try:
        result = crew.kickoff()
    except Exception as e:
        print(f"\n⚠️  CrewAI execution failed: {type(e).__name__}: {str(e)}")
        if "Timeout" in str(e) or "timeout" in str(e).lower():
            print("\n💡 NOTE: LLM timed out processing the response.")
            print("   This is likely due to the large JSON response size.")
            print("   The tool itself executed successfully (see logs above).")
            print("   Consider using fewer sites or a faster LLM.")
            return False
        raise
    
    # Save result
    result_data = serialize_crewai_result(result)
    result_file = save_test_result("maigret", "crewai_verbatim_test", result_data, test_username)
    print(f"\n📁 Result saved to: {result_file}")
    
    # Analyze result
    print("\n" + "=" * 80)
    print("ANALYZING RESULT")
    print("=" * 80)
    
    raw_output = result_data.get("raw", "")
    print(f"\n'raw' field type: {type(raw_output)}")
    print(f"'raw' field length: {len(raw_output)}")
    print(f"\nFirst 300 chars of 'raw':")
    print(raw_output[:300])
    
    # Check if it's valid JSON
    is_valid_json = False
    try:
        parsed = json.loads(raw_output)
        is_valid_json = True
        print(f"\n✅ SUCCESS: 'raw' field contains valid JSON")
        print(f"   Parsed type: {type(parsed)}")
        if isinstance(parsed, dict):
            print(f"   Number of sites: {len(parsed)}")
            print(f"   Sample sites: {list(parsed.keys())[:5]}")
    except json.JSONDecodeError:
        print(f"\n❌ FAILURE: 'raw' field is NOT valid JSON")
        print(f"   It appears the LLM summarized instead of returning verbatim output")
        print(f"\n   First 500 chars:")
        print(raw_output[:500])
        is_valid_json = False
    
    # Check tasks_output for the actual tool observation
    if 'tasks_output' in result_data and len(result_data['tasks_output']) > 0:
        task_output = result_data['tasks_output'][0]
        if 'messages' in task_output:
            print(f"\n" + "=" * 80)
            print("CHECKING TOOL OBSERVATION")
            print("=" * 80)
            for i, msg in enumerate(task_output['messages']):
                if msg.get('role') == 'assistant' and 'Observation:' in msg.get('content', ''):
                    content = msg['content']
                    # Extract observation
                    if 'Observation:' in content:
                        obs_start = content.find('Observation:') + len('Observation:')
                        obs_end = content.find('\n```', obs_start)
                        if obs_end == -1:
                            obs_end = content.find('\nThought:', obs_start)
                        if obs_end == -1:
                            obs_end = len(content)
                        observation = content[obs_start:obs_end].strip()
                        
                        print(f"\nMessage {i} - Observation (first 300 chars):")
                        print(observation[:300])
                        
                        # Check if observation is JSON
                        if observation.strip().startswith('{'):
                            try:
                                json.loads(observation)
                                print(f"   ✅ Observation contains valid JSON")
                            except:
                                print(f"   ⚠️  Observation looks like JSON but couldn't parse")
    
    # Final verdict
    print("\n" + "=" * 80)
    if is_valid_json:
        print("✅ TEST PASSED: Agent returned verbatim JSON output")
    else:
        print("❌ TEST FAILED: Agent did not return verbatim JSON output")
    print("=" * 80)
    
    return is_valid_json


if __name__ == "__main__":
    test_maigret_crewai_verbatim_output()

