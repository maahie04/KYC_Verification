import streamlit as st
import os
from document_utils import upload_document, get_user_documents, delete_document
from supabase_client import supabase, handle_auth_failure
import datetime

def documents_page():
    st.title("Document Verification")
    st.write("Upload your documents for KYC verification.")

    user_id = st.session_state.supabase_session.user.id if st.session_state.supabase_session and hasattr(st.session_state.supabase_session, 'user') and st.session_state.supabase_session.user else None

    if not user_id:
        st.error("User authentication required to access documents.")
        handle_auth_failure()
        return

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Aadhar Card *", 
        "PAN Card *", 
        "Passport", 
        "Drivers License", 
        "Voter ID"
    ])

    uploaded_docs = {
        "Aadhar Card": False,
        "PAN Card": False,
        "Passport": False,
        "Drivers License": False,
        "Voter ID": False
    }

    existing_docs = get_user_documents(user_id)
    for doc in existing_docs:
        doc_type = doc.get('document_type')
        if doc_type in uploaded_docs:
            uploaded_docs[doc_type] = True

    with tab1:
        st.subheader("Aadhar Card Upload")
        if uploaded_docs["Aadhar Card"]:
            st.success("✓ Aadhar Card already uploaded")
        else:
            aadhar_files = st.file_uploader(
                "Upload Aadhar Card (Front and Back)",
                type=["png", "jpg", "jpeg", "pdf"],
                accept_multiple_files=True,
                key="aadhar_uploader",
                help="Upload both front and back of your Aadhar Card"
            )
            if st.button("Upload Aadhar Card", key="upload_aadhar"):
                if aadhar_files and len(aadhar_files) >= 2:
                    for uploaded_file in aadhar_files:
                        upload_document(user_id, "Aadhar Card", uploaded_file)
                    st.session_state.page = "documents"
                    st.rerun()
                else:
                    st.warning("Please upload both front and back of your Aadhar Card")

    with tab2:
        st.subheader("PAN Card Upload")
        if uploaded_docs["PAN Card"]:
            st.success("✓ PAN Card already uploaded")
        else:
            pan_file = st.file_uploader(
                "Upload PAN Card",
                type=["png", "jpg", "jpeg", "pdf"],
                key="pan_uploader",
                help="Upload your PAN Card"
            )
            if st.button("Upload PAN Card", key="upload_pan"):
                if pan_file:
                    upload_document(user_id, "PAN Card", pan_file)
                    st.session_state.page = "documents"
                    st.rerun()
                else:
                    st.warning("Please select a file to upload")

    with tab3:
        st.subheader("Passport Upload")
        if uploaded_docs["Passport"]:
            st.success("✓ Passport already uploaded")
        else:
            passport_file = st.file_uploader(
                "Upload Passport",
                type=["png", "jpg", "jpeg", "pdf"],
                key="passport_uploader",
                help="Upload your Passport"
            )
            if st.button("Upload Passport", key="upload_passport"):
                if passport_file:
                    upload_document(user_id, "Passport", passport_file)
                    st.session_state.page = "documents"
                    st.rerun()
                else:
                    st.warning("Please select a file to upload")

    with tab4:
        st.subheader("Drivers License Upload")
        if uploaded_docs["Drivers License"]:
            st.success("✓ Drivers License already uploaded")
        else:
            license_files = st.file_uploader(
                "Upload Drivers License (Front and Back)",
                type=["png", "jpg", "jpeg", "pdf"],
                accept_multiple_files=True,
                key="license_uploader",
                help="Upload both front and back of your Drivers License"
            )
            if st.button("Upload Drivers License", key="upload_license"):
                if license_files and len(license_files) >= 2:
                    for uploaded_file in license_files:
                        upload_document(user_id, "Drivers License", uploaded_file)
                    st.session_state.page = "documents"
                    st.rerun()
                else:
                    st.warning("Please upload both front and back of your Drivers License")

    with tab5:
        st.subheader("Voter ID Upload")
        if uploaded_docs["Voter ID"]:
            st.success("✓ Voter ID already uploaded")
        else:
            voter_id_files = st.file_uploader(
                "Upload Voter ID (Front and Back)",
                type=["png", "jpg", "jpeg", "pdf"],
                accept_multiple_files=True,
                key="voter_uploader",
                help="Upload both front and back of your Voter ID"
            )
            if st.button("Upload Voter ID", key="upload_voter"):
                if voter_id_files and len(voter_id_files) >= 2:
                    for uploaded_file in voter_id_files:
                        upload_document(user_id, "Voter ID", uploaded_file)
                    st.session_state.page = "documents"
                    st.rerun()
                else:
                    st.warning("Please upload both front and back of your Voter ID")

    required_docs_uploaded = uploaded_docs["Aadhar Card"] and uploaded_docs["PAN Card"]
    optional_docs_uploaded = uploaded_docs["Passport"] or uploaded_docs["Drivers License"] or uploaded_docs["Voter ID"]
    
    if required_docs_uploaded and optional_docs_uploaded:
        st.session_state.documents_uploaded = True
    else:
        st.session_state.documents_uploaded = False

    st.markdown("---")
    st.subheader("Document Upload Status")
    
    status_col1, status_col2 = st.columns(2)
    
    with status_col1:
        st.write("**Required Documents:**")
        st.write(f"- {'✓' if uploaded_docs['Aadhar Card'] else '✗'} Aadhar Card")
        st.write(f"- {'✓' if uploaded_docs['PAN Card'] else '✗'} PAN Card")
    
    with status_col2:
        st.write("**Additional Documents (At least one required):**")
        st.write(f"- {'✓' if uploaded_docs['Passport'] else '✗'} Passport")
        st.write(f"- {'✓' if uploaded_docs['Drivers License'] else '✗'} Drivers License")
        st.write(f"- {'✓' if uploaded_docs['Voter ID'] else '✗'} Voter ID")
    
    if st.session_state.documents_uploaded:
        st.success("✓ All document requirements met! You can now proceed to verification.")
    else:
        st.warning("Please upload all required documents (Aadhar Card, PAN Card, and at least one additional document) to proceed.")

    st.markdown("---")
    st.subheader("Your Uploaded Documents")
    
    if existing_docs:
        for i, doc in enumerate(existing_docs):
            col1, col2 = st.columns([4, 1])

            with col1:
                st.write(f"**Type:** {doc.get('document_type', 'N/A')}")
                created_at = doc.get('created_at')
                if created_at:
                    try:
                        dt_object = datetime.datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        st.write(f"**Uploaded:** {dt_object.strftime('%Y-%m-%d %H:%M')}")
                    except (ValueError, TypeError):
                        st.write(f"**Uploaded:** {created_at}")
                else:
                    st.write(f"**Uploaded:** N/A")

                file_path = doc.get('file_path')
                file_name = os.path.basename(file_path) if file_path else 'N/A'
                st.write(f"**File:** {file_name}")

                if file_path:
                    file_ext = os.path.splitext(file_path.lower())[1]
                    if file_ext in ['.png', '.jpg', '.jpeg']:
                        try:
                            url = supabase.storage.from_("user-documents").get_public_url(file_path)
                            st.image(url, width=150, caption=file_name)
                        except Exception as url_e:
                            st.warning(f"Could not display image preview for {file_name}.")
                            st.write("[Image file]")
                    elif file_ext == '.pdf':
                        st.write("[PDF file]")

            with col2:
                doc_id = doc.get('doc_id')
                if doc_id and user_id and file_path:
                    delete_key = f"delete_{doc_id}"
                    if st.button("Delete", key=delete_key, help="Delete this document."):
                        if delete_document(doc_id, user_id, file_path):
                            st.session_state.page = "documents"
                            st.rerun()
                else:
                    st.warning("Cannot delete: Missing document info.")

            st.markdown("---")
    else:
        st.write("No documents uploaded yet.")