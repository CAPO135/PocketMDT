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
        histories = load_all_histories()
        histories[profile_id] = data
        with open(DATA_PATH, 'w') as f:
            json.dump(histories, f, indent=2)
    except (IOError, TypeError) as e:
        print(f"Error saving patient history for {profile_id}: {e}")

def get_history(profile_id):
    try:
        histories = load_all_histories()
        return histories.get(profile_id, {})
    except Exception as e:
        print(f"Error getting patient history for {profile_id}: {e}")
        return {} 