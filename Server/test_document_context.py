#!/usr/bin/env python3
"""
Test script to verify that the endocrinologist agent properly receives
document context from the vector store.
"""

import os
import sys
from dotenv import load_dotenv

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.central_orchestrator.agent import CentralOrchestratorAgent
from modules.endocrinologist.agent import EndocrinologistAgent

load_dotenv()

def test_endocrinologist_with_document_context():
    """Test that the endocrinologist agent receives document context"""
    
    print("🧪 Testing Endocrinologist Agent with Document Context")
    print("=" * 60)
    
    # Sample document content (simulating what would come from vector store)
    sample_document_content = """
    LABORATORY REPORT
    Patient: John Doe
    Date: 2024-01-15
    
    THYROID FUNCTION TESTS:
    - TSH: 4.2 mIU/L (Reference: 0.4-4.0) - ELEVATED
    - Free T4: 0.8 ng/dL (Reference: 0.8-1.8) - LOW
    - Free T3: 2.1 pg/mL (Reference: 2.3-4.2) - LOW
    
    METABOLIC MARKERS:
    - Fasting Glucose: 95 mg/dL (Normal)
    - HbA1c: 5.4% (Normal)
    - Insulin: 12 mIU/L (Reference: 3-25) - Normal
    
    SYMPTOMS REPORTED:
    - Fatigue
    - Weight gain
    - Cold intolerance
    - Dry skin
    - Constipation
    """
    
    # Test the endocrinologist agent directly
    print("1. Testing Endocrinologist Agent directly with document context:")
    endocrinologist = EndocrinologistAgent()
    
    context = {
        "user_input": "I'm feeling tired and gaining weight. What do my lab results show?",
        "document_context": sample_document_content,
        "conversation_history": [],
        "timestamp": "2024-01-15T10:00:00",
        "agent_registry": {}
    }
    
    result = endocrinologist.run(context)
    print("\nEndocrinologist Analysis:")
    print("-" * 40)
    print(result)
    print("\n" + "=" * 60)
    
    # Test through the orchestrator
    print("2. Testing through Central Orchestrator:")
    orchestrator = CentralOrchestratorAgent()
    
    user_input = "I'm feeling tired and gaining weight. What do my lab results show?"
    
    result = orchestrator.orchestrate(
        user_input=user_input,
        document_context=sample_document_content
    )
    
    print(f"\nOrchestrator Result Status: {result.get('status', 'unknown')}")
    
    if result.get('status') == 'success':
        print(f"Routed Agents: {result.get('routed_agents', [])}")
        print(f"Confidence Score: {result.get('confidence_score', 0):.2f}")
        
        if 'EndocrinologistAgent' in result.get('agent_results', {}):
            print("\nEndocrinologist Result:")
            print("-" * 40)
            print(result['agent_results']['EndocrinologistAgent']['output'])
        
        if 'summary' in result:
            print("\nSummary:")
            print("-" * 40)
            print(result['summary'])
    
    elif result.get('clarification_required'):
        print("Clarification required:")
        for question in result.get('follow_up_questions', []):
            print(f"- {question}")
    
    print("\n" + "=" * 60)
    print("✅ Test completed!")

if __name__ == "__main__":
    test_endocrinologist_with_document_context() 