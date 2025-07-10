# Flexible Agent Orchestration System

This document explains how to use the enhanced CentralOrchestratorAgent system that provides flexible, configuration-driven agent management without requiring code changes.

## Overview

The system consists of three main components:

1. **CentralOrchestratorAgent** - Main orchestrator that routes user requests to appropriate agents
2. **AgentLoader** - Dynamic agent loader that reads from configuration files
3. **AgentManager** - Command-line utility for managing agent configurations

## Key Features

- **Configuration-driven**: All agents are defined in JSON configuration files
- **Dynamic loading**: Agents are loaded at runtime without code changes
- **Flexible routing**: Uses semantic similarity to route requests to appropriate agents
- **Follow-up questions**: Automatically generates clarification questions when needed
- **Error handling**: Robust error handling with fallback mechanisms
- **Conversation history**: Maintains conversation context across multiple turns

## File Structure

```
Server/
├── config/
│   └── agent_registry.json          # Agent configuration file
├── modules/
│   ├── central_orchestrator/
│   │   ├── agent.py                 # Main orchestrator
│   │   └── agent_loader.py          # Dynamic agent loader
│   ├── gastroenterologist/
│   │   └── agent.py                 # Example specialist agent
│   └── summary/
│       └── agent.py                 # Summary agent
├── utils/
│   └── agent_manager.py             # CLI utility for managing agents
└── example_usage.py                 # Usage examples
```

## Configuration File Format

The `config/agent_registry.json` file defines all available agents:

```json
{
  "agents": {
    "GastroenterologistAgent": {
      "module_path": "modules.gastroenterologist.agent",
      "class_name": "GastroenterologistAgent",
      "description": "Analyzes gut health, liver enzyme patterns...",
      "enabled": true,
      "priority": 1,
      "tags": ["gastroenterology", "liver", "digestive"],
      "is_summary_agent": false
    },
    "SummaryAgent": {
      "module_path": "modules.summary.agent",
      "class_name": "SummaryAgent",
      "description": "Compiles insights from multiple specialists...",
      "enabled": true,
      "priority": 0,
      "tags": ["summary", "compilation"],
      "is_summary_agent": true
    }
  },
  "settings": {
    "default_confidence_threshold": 0.75,
    "max_agents_per_request": 3,
    "embedding_model": "text-embedding-ada-002",
    "summary_agent_name": "SummaryAgent",
    "enable_dynamic_loading": true,
    "fallback_questions": [
      "What specific symptoms are you experiencing?",
      "Do you have any recent test results or lab work?"
    ]
  }
}
```

## Agent Configuration Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `module_path` | string | Yes | Python module path (e.g., "modules.cardiologist.agent") |
| `class_name` | string | Yes | Agent class name |
| `description` | string | Yes | Detailed description for semantic routing |
| `enabled` | boolean | No | Whether agent is active (default: true) |
| `priority` | integer | No | Priority for routing (default: 1) |
| `tags` | array | No | Keywords for categorization |
| `is_summary_agent` | boolean | No | Whether this is the summary agent (default: false) |

## Using the Agent Manager CLI

The `agent_manager.py` utility provides a command-line interface for managing agents:

### List all agents
```bash
python utils/agent_manager.py list
```

### List all agents (including disabled)
```bash
python utils/agent_manager.py list --all
```

### Add a new agent
```bash
python utils/agent_manager.py add CardiologistAgent \
  modules.cardiologist.agent \
  CardiologistAgent \
  "Analyzes cardiovascular health, blood pressure, heart rhythm..." \
  --tags cardiology heart blood-pressure \
  --priority 1
```

### Enable/disable an agent
```bash
python utils/agent_manager.py enable CardiologistAgent
python utils/agent_manager.py disable CardiologistAgent
```

### Show agent details
```bash
python utils/agent_manager.py show GastroenterologistAgent
```

### Remove an agent
```bash
python utils/agent_manager.py remove CardiologistAgent
```

### Validate configuration
```bash
python utils/agent_manager.py validate
```

## Using the CentralOrchestratorAgent

### Basic Usage

```python
from modules.central_orchestrator.agent import CentralOrchestratorAgent

# Initialize the orchestrator
orchestrator = CentralOrchestratorAgent()

# Process a user request
result = orchestrator.orchestrate(
    user_input="I have elevated liver enzymes and abdominal pain",
    user_profile="Patient data and lab results...",
    conversation_history=[]
)

# Check the result
if result.get('clarification_required'):
    print("Need more information:")
    for question in result.get('follow_up_questions', []):
        print(f"- {question}")
elif result.get('status') == 'success':
    print("Analysis complete:")
    print(result.get('summary'))
    print(f"Routed to: {result.get('routed_agents')}")
```

### Response Format

The orchestrator returns a dictionary with the following structure:

**Success Response:**
```python
{
    "status": "success",
    "summary": "Compiled analysis from specialists...",
    "agent_results": {
        "GastroenterologistAgent": {
            "status": "success",
            "output": "Specialist analysis...",
            "timestamp": "2024-01-01T12:00:00"
        }
    },
    "confidence_score": 0.85,
    "routed_agents": ["GastroenterologistAgent"],
    "failed_agents": []
}
```

**Clarification Required:**
```python
{
    "clarification_required": True,
    "confidence_score": 0.45,
    "message": "I wasn't able to confidently identify...",
    "follow_up_questions": [
        "What specific symptoms are you experiencing?",
        "Do you have any recent test results?"
    ],
    "available_specialists": ["GastroenterologistAgent", "CardiologistAgent"]
}
```

**Error Response:**
```python
{
    "status": "error",
    "message": "All selected agents failed to process your request",
    "failed_agents": ["GastroenterologistAgent"],
    "confidence_score": 0.0
}
```

## Creating New Agents

To create a new agent:

1. **Create the agent class:**
```python
# modules/cardiologist/agent.py
from langchain.prompts import PromptTemplate
from langchain.chat_models import ChatOpenAI

class CardiologistAgent:
    def __init__(self, model_name="gpt-4", temperature=0):
        self.llm = ChatOpenAI(model=model_name, temperature=temperature)
        self.prompt_template = PromptTemplate.from_template("""
You are a clinical cardiologist AI. Analyze the following data...
{input_data}
""")

    def run(self, context):
        input_data = context.get("user_profile", "No data provided.")
        prompt = self.prompt_template.format(input_data=input_data)
        response = self.llm.predict(prompt)
        return response
```

2. **Add to configuration:**
```bash
python utils/agent_manager.py add CardiologistAgent \
  modules.cardiologist.agent \
  CardiologistAgent \
  "Analyzes cardiovascular health, blood pressure, heart rhythm, cholesterol levels, and cardiac symptoms." \
  --tags cardiology heart blood-pressure cardiovascular
```

3. **The agent is now available for routing!**

## Advanced Features

### Dynamic Agent Loading
Agents are loaded dynamically at runtime. You can:
- Add new agents without restarting the application
- Enable/disable agents without code changes
- Update agent descriptions to improve routing

### Semantic Routing
The system uses OpenAI embeddings to match user queries with agent descriptions:
- Calculates cosine similarity between user input and agent descriptions
- Routes to agents with similarity scores above the confidence threshold
- Falls back to clarification questions when confidence is low

### Conversation History
The orchestrator maintains conversation history:
```python
# Get conversation history
history = orchestrator.get_conversation_history()

# Clear history
orchestrator.clear_conversation_history()
```

### Configuration Reloading
You can reload the configuration without restarting:
```python
orchestrator.agent_loader.reload_config()
```

## Error Handling

The system includes comprehensive error handling:

- **API Errors**: Retries with exponential backoff
- **Missing Agents**: Graceful fallback to available agents
- **Configuration Errors**: Fallback to basic agent setup
- **Import Errors**: Logs warnings and continues with available agents

## Best Practices

1. **Descriptions**: Write detailed, specific descriptions for better routing
2. **Tags**: Use relevant tags for categorization
3. **Testing**: Use the validation command to check configurations
4. **Monitoring**: Check logs for agent loading and routing decisions
5. **Fallbacks**: Always provide fallback questions for unclear requests

## Troubleshooting

### Agent Not Loading
- Check the module path and class name in configuration
- Verify the agent class exists and is importable
- Use `python utils/agent_manager.py validate` to check configuration

### Poor Routing
- Improve agent descriptions with more specific details
- Add relevant tags to help with categorization
- Adjust the confidence threshold in settings

### Performance Issues
- Consider caching embeddings for frequently used descriptions
- Monitor API usage and implement rate limiting if needed
- Use appropriate model sizes for your use case

## Example Workflow

1. **Start with basic agents:**
```bash
python utils/agent_manager.py list
```

2. **Add a new specialist:**
```bash
python utils/agent_manager.py add EndocrinologistAgent \
  modules.endocrinologist.agent \
  EndocrinologistAgent \
  "Analyzes hormone levels, thyroid function, diabetes markers..." \
  --tags endocrinology hormones thyroid diabetes
```

3. **Test the new agent:**
```python
result = orchestrator.orchestrate(
    user_input="My blood sugar is high and I'm tired",
    user_profile="Patient data..."
)
```

4. **Monitor and adjust:**
```bash
python utils/agent_manager.py show EndocrinologistAgent
python utils/agent_manager.py validate
```

This flexible system allows you to easily add, remove, and configure agents without touching code, making it perfect for dynamic medical AI applications. 