#!/usr/bin/env python3
"""
Example usage of the CentralOrchestratorAgent

This file demonstrates how to use the enhanced orchestrator agent
with different types of user inputs and scenarios.
"""

import os
import json
from modules.central_orchestrator.agent import CentralOrchestratorAgent

def main():
    """Main function demonstrating orchestrator usage"""
    
    # Initialize the orchestrator
    try:
        orchestrator = CentralOrchestratorAgent()
        print("✅ CentralOrchestratorAgent initialized successfully")
    except ValueError as e:
        print(f"❌ Initialization failed: {e}")
        print("Make sure OPENAI_API_KEY is set in your environment")
        return
    
    # Example user profiles (medical data)
    sample_user_profile = """
    Patient: John Doe, Age: 45
    Recent Lab Results:
    - AST: 45 (High)
    - ALT: 52 (High)
    - ALP: 120 (Normal)
    - GGT: 85 (High)
    - Bilirubin: 1.2 (Normal)
    
    Symptoms:
    - Abdominal discomfort
    - Fatigue
    - Mild nausea after meals
    
    Current Medications:
    - None
    
    Medical History:
    - No significant medical history
    - Occasional alcohol consumption
    """
    
    # Example 1: Clear gastroenterology question
    print("\n" + "="*60)
    print("EXAMPLE 1: Clear Gastroenterology Question")
    print("="*60)
    
    user_input_1 = "I have elevated liver enzymes and abdominal pain. What could this mean?"
    
    result_1 = orchestrator.orchestrate(
        user_input=user_input_1,
        user_profile=sample_user_profile
    )
    
    print(f"User Input: {user_input_1}")
    print(f"Result Status: {result_1.get('status', 'unknown')}")
    
    if result_1.get('clarification_required'):
        print("Clarification Required:")
        print(f"Message: {result_1.get('message')}")
        print("Follow-up Questions:")
        for i, question in enumerate(result_1.get('follow_up_questions', []), 1):
            print(f"  {i}. {question}")
    elif result_1.get('status') == 'success':
        print("Summary Generated:")
        print(result_1.get('summary', 'No summary available'))
        print(f"Routed Agents: {result_1.get('routed_agents', [])}")
        print(f"Confidence Score: {result_1.get('confidence_score', 0):.2f}")
    
    # Example 2: Vague question requiring clarification
    print("\n" + "="*60)
    print("EXAMPLE 2: Vague Question Requiring Clarification")
    print("="*60)
    
    user_input_2 = "I don't feel well"
    
    result_2 = orchestrator.orchestrate(
        user_input=user_input_2,
        user_profile=sample_user_profile
    )
    
    print(f"User Input: {user_input_2}")
    print(f"Result Status: {result_2.get('status', 'unknown')}")
    
    if result_2.get('clarification_required'):
        print("Clarification Required:")
        print(f"Message: {result_2.get('message')}")
        print("Follow-up Questions:")
        for i, question in enumerate(result_2.get('follow_up_questions', []), 1):
            print(f"  {i}. {question}")
    
    # Example 3: Request for full health summary
    print("\n" + "="*60)
    print("EXAMPLE 3: Full Health Summary Request")
    print("="*60)
    
    user_input_3 = "Can you give me a full health summary of my current condition?"
    
    result_3 = orchestrator.orchestrate(
        user_input=user_input_3,
        user_profile=sample_user_profile
    )
    
    print(f"User Input: {user_input_3}")
    print(f"Result Status: {result_3.get('status', 'unknown')}")
    
    if result_3.get('status') == 'success':
        print("Full Health Summary:")
        print(result_3.get('summary', 'No summary available'))
        print(f"All Agents Used: {result_3.get('routed_agents', [])}")
    
    # Example 4: Multi-turn conversation
    print("\n" + "="*60)
    print("EXAMPLE 4: Multi-turn Conversation")
    print("="*60)
    
    # First turn - vague
    conversation_history = []
    user_input_4a = "I have some health issues"
    
    result_4a = orchestrator.orchestrate(
        user_input=user_input_4a,
        user_profile=sample_user_profile,
        conversation_history=conversation_history
    )
    
    print(f"Turn 1 - User: {user_input_4a}")
    if result_4a.get('clarification_required'):
        print("System: Clarification needed")
        conversation_history.append({
            "user_input": user_input_4a,
            "system_response": "clarification_requested",
            "follow_up_questions": result_4a.get('follow_up_questions', [])
        })
    
    # Second turn - more specific
    user_input_4b = "I have digestive problems and my liver enzymes are high"
    
    result_4b = orchestrator.orchestrate(
        user_input=user_input_4b,
        user_profile=sample_user_profile,
        conversation_history=conversation_history
    )
    
    print(f"Turn 2 - User: {user_input_4b}")
    if result_4b.get('status') == 'success':
        print("System: Analysis completed")
        print(f"Routed to: {result_4b.get('routed_agents', [])}")
        print(f"Confidence: {result_4b.get('confidence_score', 0):.2f}")
    
    # Example 5: Adding a new agent dynamically
    print("\n" + "="*60)
    print("EXAMPLE 5: Adding New Agent Dynamically")
    print("="*60)
    
    # Define a new agent class
    class CardiologistAgent:
        description = "Analyzes cardiovascular health, blood pressure, heart rhythm, cholesterol levels, and cardiac symptoms."
        
        def __init__(self, model_name="gpt-4", temperature=0):
            self.model_name = model_name
            self.temperature = temperature
        
        def run(self, context):
            return "Cardiologist analysis: Your cardiovascular health appears normal based on available data."
    
    # Add the new agent using the dynamic configuration
    orchestrator.agent_loader.add_agent_config("CardiologistAgent", {
        "module_path": "__main__",  # Since it's defined in this file
        "class_name": "CardiologistAgent",
        "description": "Analyzes cardiovascular health, blood pressure, heart rhythm, cholesterol levels, and cardiac symptoms.",
        "enabled": True,
        "priority": 1,
        "tags": ["cardiology", "heart", "blood pressure", "cardiovascular"]
    })
    
    print("✅ Added CardiologistAgent to configuration")
    
    # Test with cardiovascular question
    user_input_5 = "I'm concerned about my blood pressure and heart health"
    
    result_5 = orchestrator.orchestrate(
        user_input=user_input_5,
        user_profile=sample_user_profile
    )
    
    print(f"User Input: {user_input_5}")
    print(f"Result Status: {result_5.get('status', 'unknown')}")
    if result_5.get('status') == 'success':
        print(f"Routed Agents: {result_5.get('routed_agents', [])}")
    
    # Example 6: Error handling demonstration
    print("\n" + "="*60)
    print("EXAMPLE 6: Error Handling")
    print("="*60)
    
    # Test with malformed input
    user_input_6 = ""  # Empty input
    
    result_6 = orchestrator.orchestrate(
        user_input=user_input_6,
        user_profile=sample_user_profile
    )
    
    print(f"User Input: '{user_input_6}' (empty)")
    print(f"Result Status: {result_6.get('status', 'unknown')}")
    
    if result_6.get('clarification_required'):
        print("System handled empty input gracefully")
    
    # Print conversation history
    print("\n" + "="*60)
    print("CONVERSATION HISTORY")
    print("="*60)
    
    history = orchestrator.get_conversation_history()
    for i, turn in enumerate(history, 1):
        print(f"Turn {i}:")
        print(f"  Input: {turn.get('user_input', 'N/A')}")
        print(f"  Routed Agents: {turn.get('routed_agents', [])}")
        print(f"  Confidence: {turn.get('confidence_score', 0):.2f}")
        print()

if __name__ == "__main__":
    main() 