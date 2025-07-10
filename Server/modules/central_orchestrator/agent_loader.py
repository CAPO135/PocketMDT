"""
Dynamic Agent Loader

This module provides functionality to dynamically load agents from configuration
without requiring code changes to the main orchestrator.
"""

import json
import importlib
import logging
from typing import Dict, Any, Optional, Type, List
from pathlib import Path

logger = logging.getLogger(__name__)

class AgentLoader:
    """Handles dynamic loading of agents from configuration"""
    
    def __init__(self, config_path: str = "config/agent_registry.json"):
        self.config_path = config_path
        self.config = self._load_config()
        self.agent_cache = {}
        
    def _load_config(self) -> Dict[str, Any]:
        """Load agent configuration from JSON file"""
        try:
            config_file = Path(self.config_path)
            if not config_file.exists():
                logger.warning(f"Config file not found: {self.config_path}")
                return {"agents": {}, "settings": {}}
                
            with open(config_file, 'r') as f:
                config = json.load(f)
                logger.info(f"Loaded agent configuration from {self.config_path}")
                return config
                
        except Exception as e:
            logger.error(f"Error loading agent configuration: {e}")
            return {"agents": {}, "settings": {}}
    
    def _import_agent_class(self, module_path: str, class_name: str) -> Optional[Type]:
        """Dynamically import an agent class"""
        try:
            module = importlib.import_module(module_path)
            agent_class = getattr(module, class_name)
            logger.info(f"Successfully imported {class_name} from {module_path}")
            return agent_class
            
        except ImportError as e:
            logger.warning(f"Could not import {class_name} from {module_path}: {e}")
            return None
        except AttributeError as e:
            logger.warning(f"Class {class_name} not found in {module_path}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error importing {class_name} from {module_path}: {e}")
            return None
    
    def get_available_agents(self) -> Dict[str, Dict[str, Any]]:
        """Get all available agents from configuration"""
        return self.config.get("agents", {})
    
    def get_enabled_agents(self) -> Dict[str, Dict[str, Any]]:
        """Get only enabled agents from configuration"""
        all_agents = self.get_available_agents()
        return {
            name: config for name, config in all_agents.items() 
            if config.get("enabled", True)
        }
    
    def load_agent_class(self, agent_name: str) -> Optional[Type]:
        """Load an agent class by name"""
        if agent_name in self.agent_cache:
            return self.agent_cache[agent_name]
        
        agent_config = self.get_available_agents().get(agent_name)
        if not agent_config:
            logger.warning(f"Agent {agent_name} not found in configuration")
            return None
        
        if not agent_config.get("enabled", True):
            logger.info(f"Agent {agent_name} is disabled")
            return None
        
        module_path = agent_config.get("module_path")
        class_name = agent_config.get("class_name")
        
        if not module_path or not class_name:
            logger.error(f"Invalid configuration for agent {agent_name}")
            return None
        
        agent_class = self._import_agent_class(module_path, class_name)
        if agent_class:
            self.agent_cache[agent_name] = agent_class
        
        return agent_class
    
    def load_all_enabled_agents(self) -> Dict[str, Type]:
        """Load all enabled agent classes"""
        enabled_agents = self.get_enabled_agents()
        loaded_agents = {}
        
        for agent_name in enabled_agents:
            agent_class = self.load_agent_class(agent_name)
            if agent_class:
                loaded_agents[agent_name] = agent_class
        
        logger.info(f"Loaded {len(loaded_agents)} enabled agents")
        return loaded_agents
    
    def get_agent_description(self, agent_name: str) -> str:
        """Get description for a specific agent"""
        agent_config = self.get_available_agents().get(agent_name, {})
        return agent_config.get("description", "")
    
    def get_agent_tags(self, agent_name: str) -> List[str]:
        """Get tags for a specific agent"""
        agent_config = self.get_available_agents().get(agent_name, {})
        return agent_config.get("tags", [])
    
    def get_summary_agent_name(self) -> str:
        """Get the name of the summary agent"""
        return self.config.get("settings", {}).get("summary_agent_name", "SummaryAgent")
    
    def get_confidence_threshold(self) -> float:
        """Get the default confidence threshold"""
        return self.config.get("settings", {}).get("default_confidence_threshold", 0.75)
    
    def get_generalist_confidence_threshold(self) -> float:
        """Get the confidence threshold for GeneralistAgent routing"""
        return self.config.get("settings", {}).get("generalist_confidence_threshold", 0.3)
    
    def get_fallback_questions(self) -> List[str]:
        """Get fallback questions for clarification"""
        return self.config.get("settings", {}).get("fallback_questions", [
            "What specific symptoms are you experiencing?",
            "Do you have any recent test results or lab work?",
            "Which part of your health are you most concerned about?"
        ])
    
    def reload_config(self):
        """Reload the configuration file"""
        self.config = self._load_config()
        self.agent_cache.clear()
        logger.info("Agent configuration reloaded")
    
    def add_agent_config(self, agent_name: str, config: Dict[str, Any]):
        """Add a new agent configuration dynamically"""
        if "agents" not in self.config:
            self.config["agents"] = {}
        
        self.config["agents"][agent_name] = config
        logger.info(f"Added agent configuration for {agent_name}")
    
    def save_config(self):
        """Save the current configuration to file"""
        try:
            config_file = Path(self.config_path)
            config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            
            logger.info(f"Configuration saved to {self.config_path}")
            
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
    
    def validate_agent_config(self, agent_name: str) -> bool:
        """Validate that an agent configuration is complete and loadable"""
        agent_config = self.get_available_agents().get(agent_name)
        if not agent_config:
            return False
        
        required_fields = ["module_path", "class_name", "description"]
        for field in required_fields:
            if field not in agent_config:
                logger.error(f"Agent {agent_name} missing required field: {field}")
                return False
        
        # Try to load the agent class
        agent_class = self.load_agent_class(agent_name)
        return agent_class is not None
    
    def get_agent_metadata(self, agent_name: str) -> Dict[str, Any]:
        """Get complete metadata for an agent"""
        agent_config = self.get_available_agents().get(agent_name, {})
        if not agent_config:
            return {}
        
        return {
            "name": agent_name,
            "module_path": agent_config.get("module_path"),
            "class_name": agent_config.get("class_name"),
            "description": agent_config.get("description"),
            "enabled": agent_config.get("enabled", True),
            "priority": agent_config.get("priority", 1),
            "tags": agent_config.get("tags", []),
            "is_summary_agent": agent_config.get("is_summary_agent", False),
            "loadable": self.validate_agent_config(agent_name)
        } 