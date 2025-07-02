import streamlit as st
from supabase_client import supabase, handle_auth_failure
import os
import uuid

def upload_document(user_id, document_type, file):
    try:
        session = supabase.auth.get_session()
        if not session or not session.user or session.user.id != user_id:
            handle_auth_failure("Authentication mismatch for document upload.")
            return None

        file_ext = os.path.splitext(file.name)[1]
        storage_folder = user_id
        file_name = f"{uuid.uuid4()}{file_ext}"
        file_path = f"{storage_folder}/{file_name}"

        file_content = file.getvalue()

        with st.spinner(f"Uploading {file.name}..."):
            storage_res = supabase.storage.from_("user-documents").upload(
                path=file_path,
                file=file_content,
                file_options={"content-type": file.type}
            )

            if isinstance(storage_res, dict) and storage_res.get('error'):
                st.error(f"Storage upload failed: {storage_res['error']['message']}")
                return None

        doc_data = {
            "user_id": user_id,
            "document_type": document_type,
            "file_path": file_path,
        }

        response = supabase.table("user_documents").insert(doc_data).execute()

        if hasattr(response, 'error') and response.error:
            st.error(f"Database record creation failed: {response.error.message}")
            try:
                print(f"Debug: Attempting to clean up storage file {file_path} due to DB error...")
                cleanup_res = supabase.storage.from_("user-documents").remove([file_path])
                if isinstance(cleanup_res, dict) and cleanup_res.get('error'):
                    print(f"Debug: Failed to cleanup storage file {file_path}: {cleanup_res['error']['message']}")
                else:
                    print(f"Debug: Successfully cleaned up storage file {file_path}.")
            except Exception as cleanup_e:
                print(f"Debug: Unexpected error during storage cleanup: {cleanup_e}")
            return None

        if not hasattr(response, 'data') or not response.data:
            st.warning("Document uploaded, but database record not returned in response.")
            return doc_data

        return response.data[0]
    except Exception as e:
        st.error(f"An unexpected error occurred during document upload: {str(e)}")
        print(e)
        return None

def get_user_documents(user_id):
    try:
        session = supabase.auth.get_session()
        if not session or not session.user or session.user.id != user_id:
            handle_auth_failure("Cannot fetch documents without a valid session.")
            return []

        response = supabase.table("user_documents").select("*").eq("user_id", user_id).execute()

        if hasattr(response, 'error') and response.error:
            st.error(f"Failed to fetch documents: {response.error.message}")
            return []

        if not hasattr(response, 'data') or not response.data:
            return []

        return response.data
    except Exception as e:
        st.error(f"An unexpected error occurred while fetching documents: {str(e)}")
        return []

def delete_document(doc_id, user_id, file_path):
    try:
        session = supabase.auth.get_session()
        if not session or not session.user or session.user.id != user_id:
            handle_auth_failure("Authentication mismatch for document deletion.")
            return False

        print(f"Debug: Attempting to delete storage file: {file_path}")
        storage_res = supabase.storage.from_("user-documents").remove([file_path])

        if isinstance(storage_res, dict) and storage_res.get('error'):
            st.error(f"Failed to delete document from storage: {storage_res['error']['message']}")
            return False
        print(f"Debug: Storage file {file_path} deleted successfully.")

        print(f"Debug: Attempting to delete DB record for doc_id: {doc_id}")
        response = supabase.table("user_documents").delete().eq("doc_id", doc_id).eq("user_id", user_id).execute()

        if hasattr(response, 'error') and response.error:
            st.error(f"Failed to delete document record: {response.error.message}")
            return False

        st.success("Document deleted!")
        return True
    except Exception as e:
        st.error(f"An unexpected error occurred during document deletion: {str(e)}")
        return False