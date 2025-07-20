import requests
import json
from config import API_URL


def upload_pdfs_api(files, user_id):
    files_payload = [("files", (f.name, f.read(), "application/pdf")) for f in files]
    data = {"user_id": user_id}
    return requests.post(f"{API_URL}/upload_pdfs/", files=files_payload, data=data)

def ask_question(question, user_id, patient_history=None):
    data = {"question": question, "user_id": user_id}
    print(f"API call - user_id: {user_id}, patient_history type: {type(patient_history)}")
    
    # Enhanced validation
    if patient_history and isinstance(patient_history, dict) and patient_history:
        # Additional validation to ensure it's a proper patient history object
        if "name" in patient_history and "dob" in patient_history:
            # Convert dictionary to JSON string for form submission
            data["patient_history"] = json.dumps(patient_history)
            print(f"API call - sending patient_history: {data['patient_history'][:100]}...")
        else:
            print(f"API call - patient_history missing required fields: {list(patient_history.keys())}")
    else:
        print(f"API call - no patient_history sent (value: {patient_history})")
    
    return requests.post(f"{API_URL}/ask/", data=data)