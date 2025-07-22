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
            # Edit existing conditions
            edit_cond_idx = st.selectbox(
                "Edit Condition",
                options=["None"] + [f"{c['name']} ({c['date']})" for c in conditions],
                key="edit_cond_select"
            )
            cond_name = ""
            cond_date = datetime.date.today()
            if edit_cond_idx != "None" and conditions:
                idx = [f"{c['name']} ({c['date']})" for c in conditions].index(edit_cond_idx)
                cond_name = st.text_input("Condition Name", value=conditions[idx]["name"], key="edit_cond_name")
                cond_date = st.date_input("Date of Diagnosis", value=datetime.date.fromisoformat(conditions[idx]["date"]), key="edit_cond_date")
            remove_cond_idx = st.selectbox(
                "Remove Condition",
                options=["None"] + [f"{c['name']} ({c['date']})" for c in conditions],
                key="remove_cond_select"
            )
            new_condition = st.text_input("New Condition Name", key="new_cond_name")
            new_condition_date = st.date_input("New Condition Date", key="new_cond_date", min_value=datetime.date(1930,1,1), max_value=datetime.date.today())

            st.subheader("Medications")
            edit_med_idx = st.selectbox(
                "Edit Medication",
                options=["None"] + [f"{m['name']} ({m['dosage']}) - {m['reason']}" for m in medications],
                key="edit_med_select"
            )
            med_name = med_dosage = med_reason = ""
            if edit_med_idx != "None" and medications:
                idx = [f"{m['name']} ({m['dosage']}) - {m['reason']}" for m in medications].index(edit_med_idx)
                med_name = st.text_input("Medication Name", value=medications[idx]["name"], key="edit_med_name")
                med_dosage = st.text_input("Dosage", value=medications[idx]["dosage"], key="edit_med_dosage")
                med_reason = st.text_input("Reason", value=medications[idx]["reason"], key="edit_med_reason")
            remove_med_idx = st.selectbox(
                "Remove Medication",
                options=["None"] + [f"{m['name']} ({m['dosage']}) - {m['reason']}" for m in medications],
                key="remove_med_select"
            )
            new_med = st.text_input("New Medication Name", key="new_med_name")
            new_dosage = st.text_input("New Dosage", key="new_med_dosage")
            new_reason = st.text_input("New Reason", key="new_med_reason")

            st.subheader("Family History")
            family_history = st.text_area("Family History (comma separated)", value=",".join(history_data.get("family_history", [])))

            st.subheader("Health Goals")
            health_goals = st.text_area("Health Goals", value=history_data.get("health_goals", ""))

            st.subheader("Symptoms")
            # Edit existing symptoms
            edit_sym_idx = st.selectbox(
                "Edit Symptom",
                options=["None"] + [f"{s['symptom']} - {s['frequency']} - {s['severity']} - {s['duration']}" for s in symptoms],
                key="edit_sym_select"
            )
            sym_name = sym_freq = sym_severity = sym_duration = ""
            if edit_sym_idx != "None" and symptoms:
                idx = [f"{s['symptom']} - {s['frequency']} - {s['severity']} - {s['duration']}" for s in symptoms].index(edit_sym_idx)
                sym_name = st.text_input("Symptom", value=symptoms[idx]["symptom"], key="edit_symptom")
                sym_freq = st.text_input("Frequency", value=symptoms[idx]["frequency"], key="edit_freq")
                sym_severity = st.selectbox("Severity", ["", "Mild", "Moderate", "Severe"], index=["", "Mild", "Moderate", "Severe"].index(symptoms[idx].get("severity", "")), key="edit_severity")
                sym_duration = st.text_input("Duration", value=symptoms[idx]["duration"], key="edit_duration")
            remove_sym_idx = st.selectbox(
                "Remove Symptom",
                options=["None"] + [f"{s['symptom']} - {s['frequency']} - {s['severity']} - {s['duration']}" for s in symptoms],
                key="remove_sym_select"
            )
            new_symptom = st.text_input("New Symptom", key="new_symptom")
            new_freq = st.text_input("New Frequency", key="new_freq")
            new_severity = st.selectbox("New Severity", ["", "Mild", "Moderate", "Severe"], key="new_severity")
            new_duration = st.text_input("New Duration", key="new_duration")

            submitted = st.form_submit_button("Save/Update Profile")

            if submitted and profile_id:
                # Handle add new condition
                if new_condition:
                    conditions.append({"name": new_condition, "date": str(new_condition_date)})
                # Handle edit condition
                if edit_cond_idx != "None" and cond_name:
                    idx = [f"{c['name']} ({c['date']})" for c in conditions].index(edit_cond_idx)
                    conditions[idx] = {"name": cond_name, "date": str(cond_date)}
                # Handle remove condition
                if remove_cond_idx != "None":
                    idx = [f"{c['name']} ({c['date']})" for c in conditions].index(remove_cond_idx)
                    conditions.pop(idx)
                # Handle add new medication
                if new_med:
                    medications.append({"name": new_med, "dosage": new_dosage, "reason": new_reason})
                # Handle edit medication
                if edit_med_idx != "None" and med_name:
                    idx = [f"{m['name']} ({m['dosage']}) - {m['reason']}" for m in medications].index(edit_med_idx)
                    medications[idx] = {"name": med_name, "dosage": med_dosage, "reason": med_reason}
                # Handle remove medication
                if remove_med_idx != "None":
                    idx = [f"{m['name']} ({m['dosage']}) - {m['reason']}" for m in medications].index(remove_med_idx)
                    medications.pop(idx)
                # Handle add new symptom
                if new_symptom:
                    symptoms.append({"symptom": new_symptom, "frequency": new_freq, "severity": new_severity, "duration": new_duration})
                # Handle edit symptom
                if edit_sym_idx != "None" and sym_name:
                    idx = [f"{s['symptom']} - {s['frequency']} - {s['severity']} - {s['duration']}" for s in symptoms].index(edit_sym_idx)
                    symptoms[idx] = {"symptom": sym_name, "frequency": sym_freq, "severity": sym_severity, "duration": sym_duration}
                # Handle remove symptom
                if remove_sym_idx != "None":
                    idx = [f"{s['symptom']} - {s['frequency']} - {s['severity']} - {s['duration']}" for s in symptoms].index(remove_sym_idx)
                    symptoms.pop(idx)
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