"""
Run OSINT tool tests grouped by execution phase

Phases:
1. Foundation (Infrastructure Recon)
2. Identity & Social Intelligence
3. Threat Intelligence
4. Content & Metadata Analysis
5. Framework Tests
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


# Phase definitions based on TEST_EXECUTION_PLAN.md
PHASES = {
    1: {
        "name": "Foundation Tests (Infrastructure Recon)",
        "description": "Core infrastructure discovery tools - Run First",
        "groups": {
            "1.1": {
                "name": "Infrastructure Recon Core",
                "usecase": "#1 - Attack Surface Discovery",
                "tests": ["subfinder", "amass", "dnsdumpster", "theharvester"]
            },
            "1.2": {
                "name": "Vulnerability & Port Scanning",
                "usecase": "#8 - Vulnerability Triage",
                "tests": ["nuclei", "masscan", "zmap"]
            }
        }
    },
    2: {
        "name": "Identity & Social Intelligence",
        "description": "Identity discovery and social media intelligence",
        "groups": {
            "2.1": {
                "name": "Username Enumeration",
                "usecase": "#6 - Username Enumeration (SOCMINT)",
                "tests": ["sherlock", "maigret"]
            },
            "2.2": {
                "name": "Email Investigation",
                "usecase": "#2, #5 - Executive Protection & Breach Intelligence",
                "tests": ["holehe", "ghunt"]
            }
        }
    },
    3: {
        "name": "Threat Intelligence",
        "description": "Threat reputation and malicious indicator checking",
        "groups": {
            "3.1": {
                "name": "Threat Reputation Checks",
                "usecase": "#3, #4 - Brand Impersonation & Supply Chain Risk",
                "tests": ["abuseipdb", "urlhaus", "otx", "misp"]
            }
        }
    },
    4: {
        "name": "Content & Metadata Analysis",
        "description": "Content discovery and file analysis",
        "groups": {
            "4.1": {
                "name": "Content Discovery",
                "usecase": "#7 - Cloud Bucket Exposure",
                "tests": ["waybackurls", "scrapy"]
            },
            "4.2": {
                "name": "Dark Web Intelligence",
                "usecase": "#9 - Dark Web Monitoring",
                "tests": ["onionsearch"]
            },
            "4.3": {
                "name": "File & Metadata Analysis",
                "usecase": "#10 - Geospatial Recon (GEOINT)",
                "tests": ["exiftool", "yara"]
            }
        }
    },
    5: {
        "name": "Framework Tests",
        "description": "Comprehensive OSINT frameworks",
        "groups": {
            "5.1": {
                "name": "All-in-One Framework",
                "usecase": "Multiple (Comprehensive OSINT)",
                "tests": ["spiderfoot"]
            }
        }
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


def run_phase(phase_num: int, group: str = None):
    """Run tests for a specific phase."""
    if phase_num not in PHASES:
        print(f"❌ Invalid phase number: {phase_num}")
        print(f"Valid phases: {list(PHASES.keys())}")
        return
    
    phase = PHASES[phase_num]
    print("\n" + "="*80)
    print(f"PHASE {phase_num}: {phase['name']}")
    print("="*80)
    print(f"Description: {phase['description']}")
    print()
    
    results = {}
    
    for group_id, group_info in phase['groups'].items():
        if group and group != group_id:
            continue
            
        print(f"\n{'─'*80}")
        print(f"Group {group_id}: {group_info['name']}")
        print(f"Use Case: {group_info['usecase']}")
        print(f"{'─'*80}")
        
        group_results = {}
        for tool_name in group_info['tests']:
            print(f"\n📋 Testing: {tool_name}")
            success = run_tool_test(tool_name)
            group_results[tool_name] = "✅ Passed" if success else "❌ Failed"
        
        results[group_id] = group_results
    
    # Summary
    print("\n" + "="*80)
    print(f"PHASE {phase_num} SUMMARY")
    print("="*80)
    for group_id, group_results in results.items():
        print(f"\nGroup {group_id}:")
        for tool, status in group_results.items():
            print(f"  {status} {tool}")
    
    return results


def list_phases():
    """List all available phases."""
    print("\n" + "="*80)
    print("Available Test Phases")
    print("="*80)
    
    for phase_num, phase in PHASES.items():
        print(f"\nPhase {phase_num}: {phase['name']}")
        print(f"  Description: {phase['description']}")
        print(f"  Groups:")
        for group_id, group_info in phase['groups'].items():
            print(f"    {group_id}: {group_info['name']}")
            print(f"      Use Case: {group_info['usecase']}")
            print(f"      Tools: {', '.join(group_info['tests'])}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run OSINT tool tests by execution phase",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run Phase 1 (Foundation)
  python run_tests_by_phase.py --phase 1
  
  # Run specific group in Phase 1
  python run_tests_by_phase.py --phase 1 --group 1.1
  
  # List all phases
  python run_tests_by_phase.py --list
  
  # Run all phases sequentially
  python run_tests_by_phase.py --all
        """
    )
    
    parser.add_argument(
        '--phase',
        type=int,
        help='Phase number to run (1-5)'
    )
    
    parser.add_argument(
        '--group',
        type=str,
        help='Specific group to run within phase (e.g., "1.1")'
    )
    
    parser.add_argument(
        '--list',
        action='store_true',
        help='List all available phases and groups'
    )
    
    parser.add_argument(
        '--all',
        action='store_true',
        help='Run all phases sequentially'
    )
    
    args = parser.parse_args()
    
    if args.list:
        list_phases()
        return
    
    if args.all:
        print("="*80)
        print("Running ALL Phases Sequentially")
        print("="*80)
        for phase_num in sorted(PHASES.keys()):
            run_phase(phase_num)
        return
    
    if args.phase:
        run_phase(args.phase, args.group)
    else:
        parser.print_help()
        print("\n💡 Tip: Use --list to see all available phases")


if __name__ == "__main__":
    main()

