import json
import os

DATA_PATH = os.path.join(os.path.dirname(__file__), 'patient_histories.json')

def load_all_histories():
    if not os.path.exists(DATA_PATH):
        return {}
    try:
        with open(DATA_PATH, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError, IOError) as e:
        print(f"Error loading patient histories: {e}")
        return {}

def save_history(profile_id, data):
    try:
        print(f"save_history called for {profile_id} with data type: {type(data)}")
        histories = load_all_histories()
        histories[profile_id] = data
        print(f"Writing to {DATA_PATH}: {histories}")
        with open(DATA_PATH, 'w') as f:
            json.dump(histories, f, indent=2)
        print(f"Successfully saved profile {profile_id}")
    except (IOError, TypeError) as e:
        print(f"Error saving patient history for {profile_id}: {e}")

def get_history(profile_id):
    try:
        print(f"get_history called for {profile_id}")
        histories = load_all_histories()
        print(f"All histories: {histories}")
        history_data = histories.get(profile_id, {})
        print(f"Retrieved data for {profile_id}: {type(history_data)} - {history_data}")
        # Ensure we always return a dictionary, not a string or other type
        if not isinstance(history_data, dict):
            print(f"Warning: Patient history for {profile_id} is not a dictionary: {type(history_data)}")
            return {}
        return history_data
    except Exception as e:
        print(f"Error getting patient history for {profile_id}: {e}")
        return {} 