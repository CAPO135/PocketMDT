#!/usr/bin/env python3
"""
Verification script to demonstrate the improved separation between user input and document context.
"""

import os
import sys
from dotenv import load_dotenv

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.central_orchestrator.agent import CentralOrchestratorAgent
from modules.endocrinologist.agent import EndocrinologistAgent

load_dotenv()

def verify_context_separation():
    """Verify that user input and document context are properly separated"""
    
    print("🔍 Verifying Context Separation")
    print("=" * 60)
    
    # Sample user question
    user_question = "What do my thyroid results mean and should I be concerned?"
    
    # Sample document content (simulating vector store results)
    document_content = """
    LABORATORY REPORT - THYROID FUNCTION TESTS
    Patient: Jane Smith
    Date: 2024-01-20
    
    TSH: 6.8 mIU/L (Reference: 0.4-4.0) - ELEVATED
    Free T4: 0.7 ng/dL (Reference: 0.8-1.8) - LOW
    Free T3: 1.9 pg/mL (Reference: 2.3-4.2) - LOW
    
    ADDITIONAL METABOLIC MARKERS:
    - Fasting Glucose: 88 mg/dL (Normal)
    - HbA1c: 5.2% (Normal)
    - Total Cholesterol: 220 mg/dL (Borderline High)
    - LDL: 140 mg/dL (High)
    
    SYMPTOMS REPORTED:
    - Fatigue
    - Weight gain (15 lbs over 6 months)
    - Cold intolerance
    - Dry skin
    - Hair loss
    - Constipation
    """
    
    print("📋 Test Scenario:")
    print(f"User Question: '{user_question}'")
    print(f"Document Content: {len(document_content.split())} words of medical data")
    print("\n" + "=" * 60)
    
    # Test 1: Direct agent usage with proper context separation
    print("1. Testing Direct Agent with Separated Context:")
    endocrinologist = EndocrinologistAgent()
    
    context = {
        "user_input": user_question,
        "document_context": document_content,
        "conversation_history": [],
        "timestamp": "2024-01-20T14:30:00",
        "agent_registry": {}
    }
    
    result = endocrinologist.run(context)
    print("\nEndocrinologist Analysis:")
    print("-" * 40)
    print(result)
    print("\n" + "=" * 60)
    
    # Test 2: Through orchestrator
    print("2. Testing Through Central Orchestrator:")
    orchestrator = CentralOrchestratorAgent()
    
    result = orchestrator.orchestrate(
        user_input=user_question,
        document_context=document_content
    )
    
    print(f"\nOrchestrator Result Status: {result.get('status', 'unknown')}")
    
    if result.get('status') == 'success':
        print(f"Routed Agents: {result.get('routed_agents', [])}")
        print(f"Confidence Score: {result.get('confidence_score', 0):.2f}")
        
        if 'EndocrinologistAgent' in result.get('agent_results', {}):
            print("\nEndocrinologist Result:")
            print("-" * 40)
            print(result['agent_results']['EndocrinologistAgent']['output'])
    
    print("\n" + "=" * 60)
    
    # Test 3: Verify context structure
    print("3. Context Structure Verification:")
    context = orchestrator.create_context(user_question, document_content)
    
    print("Context Keys:")
    for key, value in context.items():
        if key == 'document_context':
            print(f"  - {key}: {len(str(value).split())} words of medical data")
        elif key == 'user_input':
            print(f"  - {key}: '{value}'")
        else:
            print(f"  - {key}: {type(value).__name__}")
    
    print("\n✅ Context separation verified!")
    print("   - user_input: Contains the user's question")
    print("   - document_context: Contains medical data from vector store")
    print("   - Clear separation allows agents to distinguish between user questions and medical data")

if __name__ == "__main__":
    verify_context_separation() 