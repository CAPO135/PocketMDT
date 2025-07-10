#!/usr/bin/env python3
"""
Test script for the GeneralistAgent implementation
"""

import os
import sys
from dotenv import load_dotenv

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.central_orchestrator.agent import CentralOrchestratorAgent
from logger import logger

def test_generalist_agent():
    """Test the GeneralistAgent with various types of questions"""
    
    # Load environment variables
    load_dotenv()
    
    # Initialize the orchestrator
    orchestrator = CentralOrchestratorAgent()
    
    # Test questions that should trigger the GeneralistAgent
    test_questions = [
        "What does this medical report mean?",
        "Can you explain these lab results?",
        "Help me understand this document",
        "What is the general overview of my health?",
        "I'm confused about these test results",
        "Tell me about what's in my medical records",
        "How do I read this medical document?",
        "What are the key points in my health data?"
    ]
    
    # Sample document context (simulating uploaded medical documents)
    sample_document_context = """
    LABORATORY RESULTS:
    - Hemoglobin: 14.2 g/dL (Normal: 12.0-15.5)
    - White Blood Cell Count: 7.5 K/μL (Normal: 4.5-11.0)
    - Platelet Count: 250 K/μL (Normal: 150-450)
    - Glucose: 95 mg/dL (Normal: 70-100)
    - Cholesterol Total: 180 mg/dL (Normal: <200)
    - HDL: 55 mg/dL (Normal: >40)
    - LDL: 100 mg/dL (Normal: <100)
    
    VITAL SIGNS:
    - Blood Pressure: 120/80 mmHg
    - Heart Rate: 72 bpm
    - Temperature: 98.6°F
    - Weight: 150 lbs
    
    MEDICAL HISTORY:
    - No significant medical history
    - No current medications
    - No known allergies
    """
    
    print("🧪 Testing GeneralistAgent Implementation")
    print("=" * 50)
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n📝 Test {i}: {question}")
        print("-" * 30)
        
        try:
            result = orchestrator.orchestrate(question, document_context=sample_document_context)
            
            if result.get("status") == "success":
                print("✅ Success!")
                print(f"📊 Confidence Score: {result.get('confidence_score', 'N/A')}")
                print(f"🤖 Routed Agents: {result.get('routed_agents', [])}")
                print(f"🔄 Fallback Used: {result.get('fallback_used', False)}")
                print(f"📄 Summary: {result.get('summary', 'N/A')[:200]}...")
            elif result.get("clarification_required"):
                print("❓ Clarification Required")
                print(f"📊 Confidence Score: {result.get('confidence_score', 'N/A')}")
                print(f"❓ Message: {result.get('message', 'N/A')}")
            else:
                print("❌ Unexpected Result")
                print(f"📊 Result: {result}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print()

def test_specialist_vs_generalist():
    """Test to ensure specialists are still preferred for specific questions"""
    
    load_dotenv()
    orchestrator = CentralOrchestratorAgent()
    
    # Questions that should go to specialists
    specialist_questions = [
        "What do my liver enzymes mean?",
        "Are my thyroid levels normal?",
        "What about my digestive symptoms?",
        "My blood sugar is high, what should I do?",
        "I have fatigue and weight gain, is it my thyroid?"
    ]
    
    sample_document_context = """
    LAB RESULTS:
    - AST: 45 U/L (Normal: 10-40)
    - ALT: 50 U/L (Normal: 7-56)
    - TSH: 4.5 mIU/L (Normal: 0.4-4.0)
    - Free T4: 0.8 ng/dL (Normal: 0.8-1.8)
    - Glucose: 110 mg/dL (Normal: 70-100)
    """
    
    print("\n🔬 Testing Specialist vs Generalist Routing")
    print("=" * 50)
    
    for i, question in enumerate(specialist_questions, 1):
        print(f"\n📝 Test {i}: {question}")
        print("-" * 30)
        
        try:
            result = orchestrator.orchestrate(question, document_context=sample_document_context)
            
            if result.get("status") == "success":
                print("✅ Success!")
                print(f"📊 Confidence Score: {result.get('confidence_score', 'N/A')}")
                print(f"🤖 Routed Agents: {result.get('routed_agents', [])}")
                print(f"🔄 Fallback Used: {result.get('fallback_used', False)}")
                print(f"📄 Summary: {result.get('summary', 'N/A')[:200]}...")
            elif result.get("clarification_required"):
                print("❓ Clarification Required")
                print(f"📊 Confidence Score: {result.get('confidence_score', 'N/A')}")
            else:
                print("❌ Unexpected Result")
                print(f"📊 Result: {result}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print()

if __name__ == "__main__":
    print("🚀 Starting GeneralistAgent Tests")
    
    # Test generalist questions
    test_generalist_agent()
    
    # Test specialist routing
    test_specialist_vs_generalist()
    
    print("\n✅ Testing Complete!") 