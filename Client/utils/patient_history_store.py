import json
import os

DATA_PATH = os.path.join(os.path.dirname(__file__), 'patient_histories.json')

def load_all_histories():
    if not os.path.exists(DATA_PATH):
        return {}
    with open(DATA_PATH, 'r') as f:
        return json.load(f)

def save_history(profile_id, data):
    histories = load_all_histories()
    histories[profile_id] = data
    with open(DATA_PATH, 'w') as f:
        json.dump(histories, f, indent=2)

def get_history(profile_id):
    return load_all_histories().get(profile_id, {}) 