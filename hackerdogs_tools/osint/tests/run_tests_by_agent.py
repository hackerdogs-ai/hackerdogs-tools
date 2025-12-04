"""
Run OSINT tool tests grouped by agent

Agents:
- Infrastructure_Recon_Agent
- Identity_Hunter_Agent
- Threat_Intel_Agent
"""

import sys
import argparse
from pathlib import Path

# Load environment variables (optional)
try:
    from dotenv import load_dotenv
    load_dotenv(override=True)
except ImportError:
    pass  # dotenv not required

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))


# Agent definitions
AGENTS = {
    "infrastructure": {
        "name": "Infrastructure Recon Agent",
        "description": "The Mapper - Maps attack surfaces, subdomains, IPs, and network assets",
        "tools": [
            "subfinder", "amass", "nuclei", "masscan", "zmap",
            "theharvester", "dnsdumpster", "waybackurls", "scrapy",
            "exiftool"
        ]
    },
    "identity": {
        "name": "Identity Hunter Agent",
        "description": "The Detective - Connects digital identifiers to real-world identities",
        "tools": [
            "sherlock", "maigret", "ghunt", "holehe"
        ]
    },
    "threat": {
        "name": "Threat Intel Agent",
        "description": "The Defender - Assesses risk levels of indicators",
        "tools": [
            "abuseipdb", "urlhaus", "otx", "misp", "onionsearch", "yara"
        ]
    }
}


def run_tool_test(tool_name: str) -> bool:
    """Run test for a specific tool."""
    try:
        import importlib
        test_module = importlib.import_module(f"hackerdogs_tools.osint.tests.test_{tool_name}")
        
        if hasattr(test_module, 'run_all_tests'):
            print(f"\n{'='*80}")
            print(f"Running {tool_name.upper()} Tests")
            print('='*80)
            test_module.run_all_tests()
            return True
        else:
            print(f"⚠️  test_{tool_name}.py does not have run_all_tests() function")
            return False
    except ImportError as e:
        print(f"❌ Failed to import test_{tool_name}: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Error running test_{tool_name}: {str(e)}")
        return False


def run_agent(agent_key: str):
    """Run tests for a specific agent."""
    if agent_key not in AGENTS:
        print(f"❌ Invalid agent: {agent_key}")
        print(f"Valid agents: {list(AGENTS.keys())}")
        return
    
    agent = AGENTS[agent_key]
    print("\n" + "="*80)
    print(f"AGENT: {agent['name']}")
    print("="*80)
    print(f"Description: {agent['description']}")
    print(f"Tools: {', '.join(agent['tools'])}")
    print()
    
    results = {}
    for tool_name in agent['tools']:
        print(f"\n📋 Testing: {tool_name}")
        success = run_tool_test(tool_name)
        results[tool_name] = "✅ Passed" if success else "❌ Failed"
    
    # Summary
    print("\n" + "="*80)
    print(f"{agent['name']} SUMMARY")
    print("="*80)
    for tool, status in results.items():
        print(f"  {status} {tool}")
    
    return results


def list_agents():
    """List all available agents."""
    print("\n" + "="*80)
    print("Available OSINT Agents")
    print("="*80)
    
    for agent_key, agent in AGENTS.items():
        print(f"\n{agent_key.upper()}: {agent['name']}")
        print(f"  Description: {agent['description']}")
        print(f"  Tools: {', '.join(agent['tools'])}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run OSINT tool tests by agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run Infrastructure Recon Agent tests
  python run_tests_by_agent.py --agent infrastructure
  
  # Run Identity Hunter Agent tests
  python run_tests_by_agent.py --agent identity
  
  # Run Threat Intel Agent tests
  python run_tests_by_agent.py --agent threat
  
  # List all agents
  python run_tests_by_agent.py --list
  
  # Run all agents sequentially
  python run_tests_by_agent.py --all
        """
    )
    
    parser.add_argument(
        '--agent',
        type=str,
        choices=list(AGENTS.keys()),
        help='Agent to run tests for'
    )
    
    parser.add_argument(
        '--list',
        action='store_true',
        help='List all available agents'
    )
    
    parser.add_argument(
        '--all',
        action='store_true',
        help='Run all agents sequentially'
    )
    
    args = parser.parse_args()
    
    if args.list:
        list_agents()
        return
    
    if args.all:
        print("="*80)
        print("Running ALL Agents Sequentially")
        print("="*80)
        for agent_key in AGENTS.keys():
            run_agent(agent_key)
        return
    
    if args.agent:
        run_agent(args.agent)
    else:
        parser.print_help()
        print("\n💡 Tip: Use --list to see all available agents")


if __name__ == "__main__":
    main()

