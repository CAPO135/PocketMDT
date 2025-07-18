import streamlit as st
from utils.api import upload_pdfs_api


def render_uploader():
    st.sidebar.header("Upload Medical documents (.PDFs)")
    uploaded_files = st.sidebar.file_uploader("Upload multiple PDFs", type="pdf", accept_multiple_files=True)
    
    # Get the current user ID from the selected profile
    user_id = None
    if "selected_profile" in st.session_state and st.session_state.selected_profile != "New Profile":
        user_id = st.session_state.selected_profile
    else:
        st.sidebar.warning("⚠️ Please select a profile in the Patient History section before uploading documents")
        return
    
    if st.sidebar.button("Upload DB") and uploaded_files and user_id:
        response = upload_pdfs_api(uploaded_files, user_id)
        if response.status_code == 200:
            st.sidebar.success(f"Uploaded successfully for {user_id}")
        else:
            st.sidebar.error(f"Error: {response.text}")
    elif uploaded_files and not user_id:
        st.sidebar.error("Please select a profile before uploading documents")