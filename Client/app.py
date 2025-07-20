import streamlit as st
from components.upload import render_uploader
from components.history_download import render_history_download
from components.chatUI import render_chat
from utils.patient_history_store import load_all_histories, save_history, get_history
import datetime

st.set_page_config(page_title="AI Pocket MDT", layout="wide")
st.title(" 🩺 Multi-Disciplinary Medical Assistant")

# --- Sidebar Navigation ---
page = st.sidebar.radio(
    "Navigation",
    ["Patient History", "Upload Medical Documents & Chat"]
)

# --- Patient History Page ---
def patient_history_page():
    st.header("Patient History Intake")
    all_histories = load_all_histories()
    profile_names = list(all_histories.keys())
    selected_profile = st.selectbox(
        "Select your profile",
        ["New Profile"] + profile_names,
        key="profile_selector"
    )
    
    # Store selected profile in session state for chat component
    st.session_state.selected_profile = selected_profile
    
    if selected_profile == "New Profile":
        profile_id = st.text_input("Enter your name (unique):", key="new_profile_name")
        history_data = {}
    else:
        profile_id = selected_profile
        history_data = get_history(profile_id)

    if profile_id:
        # Load existing lists or initialize
        conditions = history_data.get("conditions", [])
        medications = history_data.get("medications", [])
        symptoms = history_data.get("symptoms", [])

        with st.form("patient_history_form"):
            st.subheader("Demographics")
            name = profile_id if selected_profile == "New Profile" else st.text_input("Name", value=history_data.get("name", profile_id))
            
            # Handle DOB with null support
            dob_val = history_data.get("dob", None)
            if dob_val:
                try:
                    dob = st.date_input(
                        "Date of Birth",
                        value=datetime.date.fromisoformat(dob_val),
                        min_value=datetime.date(1930,1,1),
                        max_value=datetime.date.today()
                    )
                except:
                    dob = st.date_input(
                        "Date of Birth",
                        value=datetime.date(2000,1,1),
                        min_value=datetime.date(1930,1,1),
                        max_value=datetime.date.today()
                    )
            else:
                dob = st.date_input(
                    "Date of Birth",
                    value=datetime.date(2000,1,1),
                    min_value=datetime.date(1930,1,1),
                    max_value=datetime.date.today()
                )
            
            gender = st.selectbox("Gender", ["", "Male", "Female", "Other"], index=["", "Male", "Female", "Other"].index(history_data.get("gender", "")))
            
            # Height with null support
            height_ft = st.number_input("Height (feet)", min_value=0, max_value=8, value=history_data.get("height_ft", 0))
            height_in = st.number_input("Height (inches)", min_value=0, max_value=11, value=history_data.get("height_in", 0))
            weight_lbs = st.number_input("Weight (lbs)", min_value=0, value=history_data.get("weight_lbs", 0))

            st.subheader("Medical Conditions")
            
            # Display and edit existing conditions
            if conditions:
                st.markdown("**Current Conditions:**")
                for i, condition in enumerate(conditions):
                    col1, col2, col3 = st.columns([3, 2, 1])
                    with col1:
                        conditions[i]["name"] = st.text_input(f"Condition {i+1}", value=condition.get("name", ""), key=f"edit_cond_name_{i}")
                    with col2:
                        try:
                            cond_date = datetime.date.fromisoformat(condition.get("date", "2000-01-01"))
                        except:
                            cond_date = datetime.date(2000, 1, 1)
                        conditions[i]["date"] = str(st.date_input("Date", value=cond_date, key=f"edit_cond_date_{i}"))
                    with col3:
                        if st.button("Delete", key=f"del_cond_{i}"):
                            conditions.pop(i)
                            st.rerun()
            
            # Add new condition
            st.markdown("**Add New Condition**")
            col1, col2, col3 = st.columns([3, 2, 1])
            with col1:
                new_condition = st.text_input("Condition Name", key="new_cond_name")
            with col2:
                new_condition_date = st.date_input("Date of Diagnosis", key="new_cond_date", min_value=datetime.date(1930,1,1), max_value=datetime.date.today())
            with col3:
                if st.button("Add Condition", key="add_cond"):
                    if new_condition:
                        conditions.append({"name": new_condition, "date": str(new_condition_date)})
                        st.rerun()

            st.subheader("Medications")
            
            # Display and edit existing medications
            if medications:
                st.markdown("**Current Medications:**")
                for i, medication in enumerate(medications):
                    col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
                    with col1:
                        medications[i]["name"] = st.text_input(f"Medication {i+1}", value=medication.get("name", ""), key=f"edit_med_name_{i}")
                    with col2:
                        medications[i]["dosage"] = st.text_input("Dosage", value=medication.get("dosage", ""), key=f"edit_med_dosage_{i}")
                    with col3:
                        medications[i]["reason"] = st.text_input("Reason", value=medication.get("reason", ""), key=f"edit_med_reason_{i}")
                    with col4:
                        if st.button("Delete", key=f"del_med_{i}"):
                            medications.pop(i)
                            st.rerun()
            
            # Add new medication
            st.markdown("**Add New Medication**")
            col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
            with col1:
                new_med = st.text_input("Medication Name", key="new_med_name")
            with col2:
                new_dosage = st.text_input("Dosage", key="new_med_dosage")
            with col3:
                new_reason = st.text_input("Reason", key="new_med_reason")
            with col4:
                if st.button("Add Medication", key="add_med"):
                    if new_med:
                        medications.append({"name": new_med, "dosage": new_dosage, "reason": new_reason})
                        st.rerun()

            st.subheader("Family History")
            family_history = st.text_area("Family History (comma separated)", value=",".join(history_data.get("family_history", [])))

            st.subheader("Health Goals")
            health_goals = st.text_area("Health Goals", value=history_data.get("health_goals", ""))

            st.subheader("Symptoms")
            
            # Display and edit existing symptoms
            if symptoms:
                st.markdown("**Current Symptoms:**")
                for i, symptom in enumerate(symptoms):
                    col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])
                    with col1:
                        symptoms[i]["symptom"] = st.text_input(f"Symptom {i+1}", value=symptom.get("symptom", ""), key=f"edit_symptom_{i}")
                    with col2:
                        symptoms[i]["frequency"] = st.text_input("Frequency", value=symptom.get("frequency", ""), key=f"edit_freq_{i}")
                    with col3:
                        symptoms[i]["severity"] = st.selectbox("Severity", ["", "Mild", "Moderate", "Severe"], 
                                                             index=["", "Mild", "Moderate", "Severe"].index(symptom.get("severity", "")), 
                                                             key=f"edit_severity_{i}")
                    with col4:
                        symptoms[i]["duration"] = st.text_input("Duration", value=symptom.get("duration", ""), key=f"edit_duration_{i}")
                    with col5:
                        if st.button("Delete", key=f"del_symptom_{i}"):
                            symptoms.pop(i)
                            st.rerun()
            
            # Add new symptom
            st.markdown("**Add New Symptom**")
            col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])
            with col1:
                new_symptom = st.text_input("Symptom", key="new_symptom")
            with col2:
                new_freq = st.text_input("Frequency", key="new_freq")
            with col3:
                new_severity = st.selectbox("Severity", ["", "Mild", "Moderate", "Severe"], key="new_severity")
            with col4:
                new_duration = st.text_input("Duration", key="new_duration")
            with col5:
                if st.button("Add Symptom", key="add_symptom"):
                    if new_symptom:
                        symptoms.append({"symptom": new_symptom, "frequency": new_freq, "severity": new_severity, "duration": new_duration})
                        st.rerun()

            submitted = st.form_submit_button("Save/Update Profile")

            if submitted and profile_id:
                # Clean up empty values
                conditions = [c for c in conditions if c.get("name")]
                medications = [m for m in medications if m.get("name")]
                symptoms = [s for s in symptoms if s.get("symptom")]
                
                data = {
                    "name": name if name else profile_id,
                    "dob": str(dob) if dob else None,
                    "gender": gender if gender else None,
                    "height_ft": height_ft if height_ft > 0 else None,
                    "height_in": height_in if height_in > 0 else None,
                    "weight_lbs": weight_lbs if weight_lbs > 0 else None,
                    "conditions": conditions,
                    "medications": medications,
                    "family_history": [x.strip() for x in family_history.split(",") if x.strip()],
                    "health_goals": health_goals if health_goals else None,
                    "symptoms": symptoms
                }
                # Debug: Print the data being saved
                print(f"Saving profile data for {profile_id}: {data}")
                save_history(profile_id, data)
                st.success(f"Profile '{profile_id}' saved!")

# --- Main App Routing ---
if page == "Patient History":
    patient_history_page()
else:
    st.header("Upload Medical Documents & Chat")
    render_uploader()
    render_chat()
    render_history_download()