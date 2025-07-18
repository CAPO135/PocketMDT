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

# Only show the form if a profile_id is set (either new or existing)
if profile_id:
    with st.form("patient_history_form"):
        st.subheader("Demographics")
        name = profile_id if selected_profile == "New Profile" else st.text_input("Name", value=history_data.get("name", profile_id))
        dob_val = history_data.get("dob", None)
        dob = st.date_input(
            "Date of Birth",
            value=datetime.date.fromisoformat(dob_val) if dob_val else datetime.date(2000,1,1),
            min_value=datetime.date(1930,1,1),
            max_value=datetime.date.today()
        )
        gender = st.selectbox("Gender", ["Male", "Female", "Other"], index=["Male", "Female", "Other"].index(history_data.get("gender", "Male")))
        # Height in feet and inches
        height_ft = st.number_input("Height (feet)", min_value=0, max_value=8, value=history_data.get("height_ft", 0))
        height_in = st.number_input("Height (inches)", min_value=0, max_value=11, value=history_data.get("height_in", 0))
        weight_lbs = st.number_input("Weight (lbs)", min_value=0, value=history_data.get("weight_lbs", 0))

        st.subheader("Medical History")
        # Conditions: list of dicts with name and date
        conditions = history_data.get("conditions", [])
        st.markdown("**Conditions** (add each with date of diagnosis)")
        new_condition = st.text_input("Condition Name", key="cond_name")
        new_condition_date = st.date_input("Date of Diagnosis", key="cond_date", min_value=datetime.date(1930,1,1), max_value=datetime.date.today())
        if st.button("Add Condition") and new_condition:
            conditions.append({"name": new_condition, "date": str(new_condition_date)})
        if conditions:
            for i, cond in enumerate(conditions):
                st.write(f"{cond['name']} (Diagnosed: {cond['date']})")
                if st.button(f"Remove Condition {i+1}"):
                    conditions.pop(i)
                    st.experimental_rerun()

        # Medications: list of dicts with name, dosage, reason
        medications = history_data.get("medications", [])
        st.markdown("**Medications** (add each with dosage and reason)")
        new_med = st.text_input("Medication Name", key="med_name")
        new_dosage = st.text_input("Dosage", key="med_dosage")
        new_reason = st.text_input("Reason", key="med_reason")
        if st.button("Add Medication") and new_med:
            medications.append({"name": new_med, "dosage": new_dosage, "reason": new_reason})
        if medications:
            for i, med in enumerate(medications):
                st.write(f"{med['name']} ({med['dosage']}) - {med['reason']}")
                if st.button(f"Remove Medication {i+1}"):
                    medications.pop(i)
                    st.experimental_rerun()

        family_history = st.text_area("Family History (comma separated)", value=",".join(history_data.get("family_history", [])))

        st.subheader("Goals")
        health_goals = st.text_area("Health Goals", value=history_data.get("health_goals", ""))

        st.subheader("Symptoms")
        # Symptoms: list of dicts with symptom, frequency, severity, duration
        symptoms = history_data.get("symptoms", [])
        new_symptom = st.text_input("Symptom", key="symptom")
        new_freq = st.text_input("Frequency (e.g. daily, weekly)", key="freq")
        new_severity = st.selectbox("Severity", ["Mild", "Moderate", "Severe"], key="severity")
        new_duration = st.text_input("Duration (e.g. 2 weeks)", key="duration")
        if st.button("Add Symptom") and new_symptom:
            symptoms.append({"symptom": new_symptom, "frequency": new_freq, "severity": new_severity, "duration": new_duration})
        if symptoms:
            for i, sym in enumerate(symptoms):
                st.write(f"{sym['symptom']} - {sym['frequency']} - {sym['severity']} - {sym['duration']}")
                if st.button(f"Remove Symptom {i+1}"):
                    symptoms.pop(i)
                    st.experimental_rerun()

        submitted = st.form_submit_button("Save/Update Profile")

        if submitted and profile_id:
            data = {
                "name": name,
                "dob": str(dob),
                "gender": gender,
                "height_ft": height_ft,
                "height_in": height_in,
                "weight_lbs": weight_lbs,
                "conditions": conditions,
                "medications": medications,
                "family_history": [x.strip() for x in family_history.split(",") if x.strip()],
                "health_goals": health_goals,
                "symptoms": symptoms
            }
            save_history(profile_id, data)
            st.success(f"Profile '{profile_id}' saved!")

# --- Existing App Components ---
render_uploader()
render_chat()
render_history_download()