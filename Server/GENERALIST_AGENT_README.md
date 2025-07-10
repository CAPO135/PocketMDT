# GeneralistAgent Implementation

## Overview

The GeneralistAgent is a new addition to the medical AI system that provides a better user experience by handling general questions about medical documents when no specific specialist is identified. Instead of asking users for clarification, the system now provides helpful responses for general inquiries.

## Problem Solved

### Before GeneralistAgent:
- Users asking general questions like "What does this report mean?" would get a clarification message
- The system would ask for more specific symptoms or details
- Users had to rephrase their questions to match specialist domains
- Poor user experience for general document interpretation requests

### After GeneralistAgent:
- General questions are handled by a dedicated generalist agent
- Users get immediate, helpful responses about their medical documents
- The system can explain medical terms, provide overviews, and offer general insights
- Better user experience with fewer clarification requests

## How It Works

### 1. Intelligent Routing
The system uses multiple strategies to determine when to use the GeneralistAgent:

**Keyword Detection:**
- Identifies general question patterns like "explain", "help me understand", "what does this mean"
- Recognizes educational requests and document interpretation needs

**Confidence-Based Routing:**
- Uses a lower confidence threshold (0.3) for the GeneralistAgent vs specialists (0.75)
- Prefers specialists for specific medical questions
- Falls back to GeneralistAgent for general questions when specialist confidence is low

### 2. Fallback Mechanism
When no specialist is identified with high confidence:
1. System attempts to use GeneralistAgent
2. If GeneralistAgent succeeds, returns helpful response
3. If GeneralistAgent fails, falls back to clarification questions

### 3. Response Structure
The GeneralistAgent provides structured responses:
1. **Summary of Findings** - What was found in the documents
2. **General Interpretation** - Explanation of the data
3. **Educational Information** - Context about relevant health concepts
4. **Follow-up Suggestions** - When to consult specialists

## Configuration

### Agent Registry Entry
```json
{
  "GeneralistAgent": {
    "module_path": "modules.generalist.agent",
    "class_name": "GeneralistAgent",
    "description": "A general medical AI assistant that can answer general questions about medical documents, provide overviews of health data, explain medical terms, and offer general health insights. Handles questions that don't require specialized expertise from specific medical specialists.",
    "enabled": true,
    "priority": 0,
    "tags": ["general", "overview", "education", "interpretation", "fallback"],
    "is_summary_agent": false
  }
}
```

### Settings
```json
{
  "settings": {
    "default_confidence_threshold": 0.75,
    "generalist_confidence_threshold": 0.3,
    "max_agents_per_request": 3
  }
}
```

## Example Usage

### General Questions (Handled by GeneralistAgent)
- "What does this medical report mean?"
- "Can you explain these lab results?"
- "Help me understand this document"
- "What is the general overview of my health?"
- "I'm confused about these test results"

### Specialist Questions (Still handled by specialists)
- "What do my liver enzymes mean?" → GastroenterologistAgent
- "Are my thyroid levels normal?" → EndocrinologistAgent
- "What about my digestive symptoms?" → GastroenterologistAgent

## Testing

Run the test script to verify the implementation:

```bash
cd Server
python test_generalist_agent.py
```

This will test:
- General questions that should trigger GeneralistAgent
- Specialist questions that should still go to specialists
- Confidence scoring and routing logic
- Fallback mechanisms

## Benefits

1. **Improved User Experience**: Users get immediate responses to general questions
2. **Better Document Understanding**: Helps users interpret medical documents
3. **Educational Value**: Provides context and explanations for medical concepts
4. **Reduced Clarification Requests**: Fewer back-and-forth interactions
5. **Maintains Specialist Expertise**: Specific medical questions still go to specialists

## Technical Implementation

### Files Modified
- `Server/modules/generalist/agent.py` - New GeneralistAgent class
- `Server/modules/generalist/__init__.py` - Module initialization
- `Server/config/agent_registry.json` - Agent configuration
- `Server/modules/central_orchestrator/agent.py` - Routing logic updates
- `Server/modules/central_orchestrator/agent_loader.py` - Configuration methods

### Key Features
- **Dynamic Loading**: GeneralistAgent loads like other agents
- **Configurable Thresholds**: Separate confidence thresholds for generalist vs specialists
- **Intelligent Routing**: Keyword detection + semantic similarity
- **Graceful Fallback**: Falls back to clarification if GeneralistAgent fails
- **Structured Responses**: Consistent response format for better UX

## Future Enhancements

1. **Learning from Interactions**: Improve routing based on user feedback
2. **Customizable Keywords**: Allow configuration of general question patterns
3. **Multi-language Support**: Extend to other languages
4. **Context Awareness**: Better understanding of conversation history
5. **Specialist Collaboration**: Allow GeneralistAgent to consult specialists when needed 