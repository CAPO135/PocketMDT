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
    # Load existing lists or initialize
    conditions = history_data.get("conditions", [])
    medications = history_data.get("medications", [])
    symptoms = history_data.get("symptoms", [])

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
        height_ft = st.number_input("Height (feet)", min_value=0, max_value=8, value=history_data.get("height_ft", 0))
        height_in = st.number_input("Height (inches)", min_value=0, max_value=11, value=history_data.get("height_in", 0))
        weight_lbs = st.number_input("Weight (lbs)", min_value=0, value=history_data.get("weight_lbs", 0))

        st.subheader("Medical History")
        # Add new condition
        st.markdown("**Add Condition** (with date of diagnosis)")
        new_condition = st.text_input("Condition Name", key="cond_name")
        new_condition_date = st.date_input("Date of Diagnosis", key="cond_date", min_value=datetime.date(1930,1,1), max_value=datetime.date.today())
        # Remove condition
        remove_condition = st.selectbox(
            "Remove a condition (optional)",
            options=["None"] + [f"{c['name']} ({c['date']})" for c in conditions],
            key="remove_condition"
        )
        if conditions:
            st.markdown("**Current Conditions:**")
            for cond in conditions:
                st.write(f"{cond['name']} (Diagnosed: {cond['date']})")

        # Add new medication
        st.markdown("**Add Medication** (with dosage and reason)")
        new_med = st.text_input("Medication Name", key="med_name")
        new_dosage = st.text_input("Dosage", key="med_dosage")
        new_reason = st.text_input("Reason", key="med_reason")
        # Remove medication
        remove_med = st.selectbox(
            "Remove a medication (optional)",
            options=["None"] + [f"{m['name']} ({m['dosage']}) - {m['reason']}" for m in medications],
            key="remove_med"
        )
        if medications:
            st.markdown("**Current Medications:**")
            for med in medications:
                st.write(f"{med['name']} ({med['dosage']}) - {med['reason']}")

        family_history = st.text_area("Family History (comma separated)", value=",".join(history_data.get("family_history", [])))

        st.subheader("Goals")
        health_goals = st.text_area("Health Goals", value=history_data.get("health_goals", ""))

        st.subheader("Symptoms")
        # Add new symptom
        new_symptom = st.text_input("Symptom", key="symptom")
        new_freq = st.text_input("Frequency (e.g. daily, weekly)", key="freq")
        new_severity = st.selectbox("Severity", ["Mild", "Moderate", "Severe"], key="severity")
        new_duration = st.text_input("Duration (e.g. 2 weeks)", key="duration")
        # Remove symptom
        remove_symptom = st.selectbox(
            "Remove a symptom (optional)",
            options=["None"] + [f"{s['symptom']} - {s['frequency']} - {s['severity']} - {s['duration']}" for s in symptoms],
            key="remove_symptom"
        )
        if symptoms:
            st.markdown("**Current Symptoms:**")
            for sym in symptoms:
                st.write(f"{sym['symptom']} - {sym['frequency']} - {sym['severity']} - {sym['duration']}")

        submitted = st.form_submit_button("Save/Update Profile")

        if submitted and profile_id:
            # Add new condition if provided
            if new_condition:
                conditions.append({"name": new_condition, "date": str(new_condition_date)})
            # Remove selected condition if chosen
            if remove_condition != "None":
                idx = [f"{c['name']} ({c['date']})" for c in conditions].index(remove_condition)
                conditions.pop(idx)
            # Add new medication if provided
            if new_med:
                medications.append({"name": new_med, "dosage": new_dosage, "reason": new_reason})
            # Remove selected medication if chosen
            if remove_med != "None":
                idx = [f"{m['name']} ({m['dosage']}) - {m['reason']}" for m in medications].index(remove_med)
                medications.pop(idx)
            # Add new symptom if provided
            if new_symptom:
                symptoms.append({"symptom": new_symptom, "frequency": new_freq, "severity": new_severity, "duration": new_duration})
            # Remove selected symptom if chosen
            if remove_symptom != "None":
                idx = [f"{s['symptom']} - {s['frequency']} - {s['severity']} - {s['duration']}" for s in symptoms].index(remove_symptom)
                symptoms.pop(idx)
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