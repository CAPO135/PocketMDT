import streamlit as st
from components.upload import render_uploader
from components.history_download import render_history_download
from components.chatUI import render_chat
from utils.patient_history_store import load_all_histories, save_history, get_history
import datetime

st.set_page_config(page_title="AI Pocket MDT",layout="wide")
st.title(" 🩺 Multi-Disciplinary Medical Assistant")

# --- Patient History Profile Selector and Form ---
st.header("Patient History Intake")

# 1. Profile selector
all_histories = load_all_histories()
profile_names = list(all_histories.keys())
selected_profile = st.selectbox("Select your profile", ["New Profile"] + profile_names)

if selected_profile == "New Profile":
    profile_id = st.text_input("Enter your name (unique):")
    history_data = {}
else:
    profile_id = selected_profile
    history_data = get_history(profile_id)

# 2. Patient history form (pre-fill if editing)
with st.form("patient_history_form"):
    name = st.text_input("Name", value=history_data.get("name", ""))
    dob_val = history_data.get("dob", None)
    dob = st.date_input("Date of Birth", value=datetime.date.fromisoformat(dob_val) if dob_val else datetime.date(2000,1,1))
    sex = st.selectbox("Sex", ["Male", "Female", "Other"], index=["Male", "Female", "Other"].index(history_data.get("sex", "Male")))
    height = st.number_input("Height (cm)", value=history_data.get("height", 0))
    weight = st.number_input("Weight (kg)", value=history_data.get("weight", 0))
    family_history = st.text_area("Family History (comma separated)", value=",".join(history_data.get("family_history", [])))
    medications = st.text_area("Current Medications (comma separated)", value=",".join(history_data.get("medications", [])))
    # ... more fields as needed ...
    submitted = st.form_submit_button("Save/Update Profile")

    if submitted and profile_id:
        data = {
            "name": name,
            "dob": str(dob),
            "sex": sex,
            "height": height,
            "weight": weight,
            "family_history": [x.strip() for x in family_history.split(",") if x.strip()],
            "medications": [x.strip() for x in medications.split(",") if x.strip()],
            # ... more fields ...
        }
        save_history(profile_id, data)
        st.success(f"Profile '{profile_id}' saved!")

# --- Existing App Components ---
render_uploader()
render_chat()
render_history_download()