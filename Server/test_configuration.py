#!/usr/bin/env python3
"""
Test script to demonstrate the new configuration validation system
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from Server.modules.central_orchestrator.agent import CentralOrchestratorAgent

def test_configuration_validation():
    """Test the configuration validation system"""
    print("Testing Central Orchestrator Agent Configuration Validation")
    print("=" * 60)
    
    try:
        # Initialize the agent
        agent = CentralOrchestratorAgent()
        
        # Get configuration status
        status = agent.get_configuration_status()
        
        print(f"Configuration Valid: {status['valid']}")
        print(f"Enabled Agents: {status['enabled_agents']}")
        print(f"Summary Agent: {status['summary_agent']}")
        
        if not status['valid']:
            print("\nConfiguration Issues:")
            for issue in status['issues']:
                print(f"  • {issue}")
            
            print("\nHelp Message:")
            print(status['help_message'])
        else:
            print("\n✅ Configuration is valid!")
            
            # Test a simple orchestration
            print("\nTesting orchestration with a sample query...")
            result = agent.orchestrate("I have digestive issues and want to understand my gut health")
            
            if result.get("status") == "configuration_error":
                print("❌ Configuration error detected during orchestration")
                print(result.get("message"))
            else:
                print("✅ Orchestration completed successfully")
                print(f"Result status: {result.get('status', 'unknown')}")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_configuration_validation() 