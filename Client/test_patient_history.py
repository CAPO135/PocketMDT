#!/usr/bin/env python3
"""
Test script to check patient history functionality
"""

import sys
import os
from pathlib import Path

# Add the current directory to Python path
sys.path.append(str(Path(__file__).parent))

from utils.patient_history_store import save_history, get_history, load_all_histories

def test_patient_history():
    """Test patient history storage and retrieval"""
    print("🧪 Testing Patient History Functionality")
    print("=" * 50)
    
    # Test data
    test_profile = "William L"
    test_data = {
        "name": "William L",
        "dob": "1990-01-01",
        "gender": "Male",
        "height_ft": 6,
        "height_in": 0,
        "weight_lbs": 180,
        "conditions": [],
        "medications": [],
        "family_history": ["Diabetes", "Heart Disease"],
        "health_goals": "Improve overall health",
        "symptoms": [
            {
                "symptom": "Fatigue",
                "frequency": "Daily",
                "severity": "Moderate",
                "duration": "2 weeks"
            }
        ]
    }
    
    print(f"📝 Test data: {test_data}")
    print()
    
    # Test save
    print("💾 Testing save_history...")
    save_history(test_profile, test_data)
    print()
    
    # Test load all
    print("📂 Testing load_all_histories...")
    all_histories = load_all_histories()
    print(f"All histories: {all_histories}")
    print()
    
    # Test get specific
    print("🔍 Testing get_history...")
    retrieved_data = get_history(test_profile)
    print(f"Retrieved data: {retrieved_data}")
    print()
    
    # Test API call simulation
    print("🌐 Testing API call simulation...")
    from utils.api import ask_question
    import json
    
    # Simulate what the API would receive
    if retrieved_data and isinstance(retrieved_data, dict) and retrieved_data:
        json_data = json.dumps(retrieved_data)
        print(f"JSON data that would be sent: {json_data[:200]}...")
    else:
        print("No valid data to send")
    
    print()
    print("✅ Test complete!")

if __name__ == "__main__":
    test_patient_history() 