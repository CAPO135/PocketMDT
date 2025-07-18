import requests
from config import API_URL


def upload_pdfs_api(files, user_id):
    files_payload = [("files", (f.name, f.read(), "application/pdf")) for f in files]
    data = {"user_id": user_id}
    return requests.post(f"{API_URL}/upload_pdfs/", files=files_payload, data=data)

def ask_question(question, user_id, patient_history=None):
    data = {"question": question, "user_id": user_id}
    if patient_history:
        data["patient_history"] = patient_history
    return requests.post(f"{API_URL}/ask/", data=data)