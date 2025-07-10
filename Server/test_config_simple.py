#!/usr/bin/env python3
"""
Simple test script to test configuration validation without requiring OpenAI API
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Mock OpenAI API key for testing
os.environ["OPENAI_API_KEY"] = "test-key"

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
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_configuration_validation() 