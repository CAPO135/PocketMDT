#!/usr/bin/env python3
"""
Agent Manager Utility

This utility provides a command-line interface to manage the agent registry
configuration without requiring code changes.
"""

import json
import argparse
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add project root to sys.path for dynamic imports
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

class AgentManager:
    """Manages agent registry configuration"""
    
    def __init__(self, config_path: str = "config/agent_registry.json"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load the current configuration"""
        if not self.config_path.exists():
            return {"agents": {}, "settings": {}}
        
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
            return {"agents": {}, "settings": {}}
    
    def _save_config(self):
        """Save the current configuration"""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def list_agents(self, show_disabled: bool = False):
        """List all agents"""
        agents = self.config.get("agents", {})
        
        if not agents:
            print("No agents configured.")
            return
        
        print(f"\n{'Agent Name':<25} {'Status':<10} {'Priority':<8} {'Tags'}")
        print("-" * 70)
        
        for name, config in agents.items():
            if not show_disabled and not config.get("enabled", True):
                continue
            
            status = "Enabled" if config.get("enabled", True) else "Disabled"
            priority = config.get("priority", 1)
            tags = ", ".join(config.get("tags", []))
            
            print(f"{name:<25} {status:<10} {priority:<8} {tags}")
    
    def _extract_agent_description(self, module_path: str, class_name: str) -> str:
        """Extract description from agent class if available"""
        import importlib
        tried_paths = [module_path]
        # If not already prefixed, try with 'Server.' as well
        if not module_path.startswith('Server.'):
            tried_paths.append(f'Server.{module_path}')
        for mod_path in tried_paths:
            try:
                module = importlib.import_module(mod_path)
                agent_class = getattr(module, class_name)
                # Try to get description from class attribute
                if hasattr(agent_class, 'description'):
                    return agent_class.description
                # Try to get docstring from class
                if agent_class.__doc__:
                    return agent_class.__doc__.strip()
                return "No description available"
            except Exception as e:
                last_error = e
                continue
        print(f"⚠️  Warning: Could not extract description from {module_path}.{class_name}: {last_error}")
        return "No description available"
    
    def add_agent(self, name: str, module_path: str, class_name: str, 
                  description: Optional[str] = None, tags: Optional[List[str]] = None, priority: int = 1):
        """Add a new agent"""
        if "agents" not in self.config:
            self.config["agents"] = {}
        
        # Extract description from agent class if not provided
        if description is None:
            description = self._extract_agent_description(module_path, class_name)
            print(f"📝 Extracted description: {description[:100]}{'...' if len(description) > 100 else ''}")
        
        self.config["agents"][name] = {
            "module_path": module_path,
            "class_name": class_name,
            "description": description,
            "enabled": True,
            "priority": priority,
            "tags": tags if tags is not None else [],
            "is_summary_agent": False
        }
        
        self._save_config()
        print(f"✅ Added agent: {name}")
    
    def remove_agent(self, name: str):
        """Remove an agent"""
        if "agents" not in self.config:
            print("No agents configured.")
            return
        
        if name in self.config["agents"]:
            del self.config["agents"][name]
            self._save_config()
            print(f"✅ Removed agent: {name}")
        else:
            print(f"❌ Agent not found: {name}")
    
    def enable_agent(self, name: str):
        """Enable an agent"""
        if "agents" not in self.config:
            print("No agents configured.")
            return
        
        if name in self.config["agents"]:
            self.config["agents"][name]["enabled"] = True
            self._save_config()
            print(f"✅ Enabled agent: {name}")
        else:
            print(f"❌ Agent not found: {name}")
    
    def disable_agent(self, name: str):
        """Disable an agent"""
        if "agents" not in self.config:
            print("No agents configured.")
            return
        
        if name in self.config["agents"]:
            self.config["agents"][name]["enabled"] = False
            self._save_config()
            print(f"✅ Disabled agent: {name}")
        else:
            print(f"❌ Agent not found: {name}")
    
    def update_agent(self, name: str, **kwargs):
        """Update agent configuration"""
        if "agents" not in self.config:
            print("No agents configured.")
            return
        
        if name not in self.config["agents"]:
            print(f"❌ Agent not found: {name}")
            return
        
        agent_config = self.config["agents"][name]
        for key, value in kwargs.items():
            if key in agent_config:
                agent_config[key] = value
            else:
                print(f"⚠️  Unknown field: {key}")
        
        self._save_config()
        print(f"✅ Updated agent: {name}")
    
    def show_agent(self, name: str):
        """Show detailed information about an agent"""
        if "agents" not in self.config:
            print("No agents configured.")
            return
        
        if name not in self.config["agents"]:
            print(f"❌ Agent not found: {name}")
            return
        
        agent_config = self.config["agents"][name]
        print(f"\nAgent: {name}")
        print("-" * 50)
        print(f"Module Path: {agent_config.get('module_path')}")
        print(f"Class Name: {agent_config.get('class_name')}")
        print(f"Enabled: {agent_config.get('enabled', True)}")
        print(f"Priority: {agent_config.get('priority', 1)}")
        print(f"Tags: {', '.join(agent_config.get('tags', []))}")
        print(f"Summary Agent: {agent_config.get('is_summary_agent', False)}")
        print(f"\nDescription:")
        print(agent_config.get('description', 'No description'))
    
    def extract_description(self, module_path: str, class_name: str):
        """Extract and display description from an agent class"""
        description = self._extract_agent_description(module_path, class_name)
        print(f"\nAgent: {class_name}")
        print(f"Module: {module_path}")
        print("-" * 50)
        print(f"Description: {description}")
        return description
    
    def validate_config(self):
        """Validate the current configuration"""
        if "agents" not in self.config:
            print("❌ No agents section in configuration")
            return False
        
        agents = self.config["agents"]
        if not agents:
            print("⚠️  No agents configured")
            return True
        
        valid = True
        summary_agents = []
        
        for name, config in agents.items():
            print(f"\nValidating {name}...")
            
            # Check required fields
            required_fields = ["module_path", "class_name", "description"]
            for field in required_fields:
                if field not in config:
                    print(f"  ❌ Missing required field: {field}")
                    valid = False
            
            # Try to load the agent class
            try:
                import importlib
                module = importlib.import_module(config["module_path"])
                agent_class = getattr(module, config["class_name"])
                print(f"  ✅ Agent class can be loaded")
                
                # Check if description matches class description
                if hasattr(agent_class, 'description'):
                    class_description = agent_class.description
                    config_description = config.get("description", "")
                    if class_description != config_description:
                        print(f"  ⚠️  Description mismatch - class has: {class_description[:50]}...")
                    else:
                        print(f"  ✅ Description matches class definition")
                        
            except Exception as e:
                print(f"  ❌ Cannot load agent class: {e}")
                valid = False
            
            # Check for summary agents
            if config.get("is_summary_agent", False):
                summary_agents.append(name)
            
            # Check if enabled
            if config.get("enabled", True):
                print(f"  ✅ {name} is enabled")
            else:
                print(f"  ⚠️  {name} is disabled")
        
        # Check summary agent configuration
        if len(summary_agents) > 1:
            print(f"  ⚠️  Multiple summary agents found: {summary_agents}")
        elif len(summary_agents) == 0:
            print("  ⚠️  No summary agent configured")
        else:
            print(f"  ✅ Summary agent: {summary_agents[0]}")
        
        return valid

def main():
    parser = argparse.ArgumentParser(description="Manage agent registry configuration")
    parser.add_argument("--config", default="config/agent_registry.json", 
                       help="Path to agent registry configuration file")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List all agents")
    list_parser.add_argument("--all", action="store_true", help="Show disabled agents too")
    
    # Add command
    add_parser = subparsers.add_parser("add", help="Add a new agent")
    add_parser.add_argument("name", help="Agent name")
    add_parser.add_argument("module_path", help="Python module path")
    add_parser.add_argument("class_name", help="Agent class name")
    add_parser.add_argument("--description", help="Agent description (will be extracted from agent class if not provided)")
    add_parser.add_argument("--tags", nargs="*", help="Agent tags")
    add_parser.add_argument("--priority", type=int, default=1, help="Agent priority")
    
    # Remove command
    remove_parser = subparsers.add_parser("remove", help="Remove an agent")
    remove_parser.add_argument("name", help="Agent name")
    
    # Enable command
    enable_parser = subparsers.add_parser("enable", help="Enable an agent")
    enable_parser.add_argument("name", help="Agent name")
    
    # Disable command
    disable_parser = subparsers.add_parser("disable", help="Disable an agent")
    disable_parser.add_argument("name", help="Agent name")
    
    # Show command
    show_parser = subparsers.add_parser("show", help="Show agent details")
    show_parser.add_argument("name", help="Agent name")
    
    # Extract description command
    extract_parser = subparsers.add_parser("extract", help="Extract description from agent class")
    extract_parser.add_argument("module_path", help="Python module path")
    extract_parser.add_argument("class_name", help="Agent class name")
    
    # Validate command
    subparsers.add_parser("validate", help="Validate configuration")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    manager = AgentManager(args.config)
    
    if args.command == "list":
        manager.list_agents(show_disabled=args.all)
    elif args.command == "add":
        manager.add_agent(
            name=args.name,
            module_path=args.module_path,
            class_name=args.class_name,
            description=args.description,
            tags=args.tags,
            priority=args.priority
        )
    elif args.command == "remove":
        manager.remove_agent(args.name)
    elif args.command == "enable":
        manager.enable_agent(args.name)
    elif args.command == "disable":
        manager.disable_agent(args.name)
    elif args.command == "show":
        manager.show_agent(args.name)
    elif args.command == "extract":
        manager.extract_description(args.module_path, args.class_name)
    elif args.command == "validate":
        if manager.validate_config():
            print("\n✅ Configuration is valid")
        else:
            print("\n❌ Configuration has issues")
            sys.exit(1)

if __name__ == "__main__":
    main() 