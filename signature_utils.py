import streamlit as st
from supabase_client import supabase, handle_auth_failure
import os
import uuid
from io import BytesIO
from PIL import Image
import numpy as np

def upload_signature(user_id, document_type, file, is_drawn=False):
    """
    Upload a signature to Supabase storage and create a database record
    
    Args:
        user_id: The user's ID
        document_type: Either 'drawn_signature' or 'written_signature'
        file: The signature file (either uploaded file or drawn image data)
        is_drawn: Boolean indicating if this is a drawn signature
    
    Returns:
        The created record or None if failed
    """
    try:
        session = supabase.auth.get_session()
        if not session or not session.user or session.user.id != user_id:
            handle_auth_failure("Authentication mismatch for signature upload.")
            return None

        # Handle drawn signature (convert from image data to bytes)
        if is_drawn:
            # Convert the numpy array to PIL Image
            img = Image.fromarray(file.astype('uint8'))
            # Convert to bytes
            byte_arr = BytesIO()
            img.save(byte_arr, format='PNG')
            file_content = byte_arr.getvalue()
            file_ext = '.png'
        else:
            # Regular file upload
            file_ext = os.path.splitext(file.name)[1]
            file_content = file.getvalue()

        storage_folder = user_id
        file_name = f"{uuid.uuid4()}{file_ext}"
        file_path = f"{storage_folder}/{file_name}"

        with st.spinner(f"Uploading {document_type.replace('_', ' ')}..."):
            storage_res = supabase.storage.from_("user-signatures").upload(
                path=file_path,
                file=file_content,
                file_options={"content-type": "image/png" if is_drawn else file.type}
            )

            if isinstance(storage_res, dict) and storage_res.get('error'):
                st.error(f"Storage upload failed: {storage_res['error']['message']}")
                return None

        doc_data = {
            "user_id": user_id,
            "document_type": document_type,
            "file_path": file_path,
        }

        response = supabase.table("user_signatures").insert(doc_data).execute()

        if hasattr(response, 'error') and response.error:
            st.error(f"Database record creation failed: {response.error.message}")
            try:
                print(f"Debug: Attempting to clean up storage file {file_path} due to DB error...")
                cleanup_res = supabase.storage.from_("user-signatures").remove([file_path])
                if isinstance(cleanup_res, dict) and cleanup_res.get('error'):
                    print(f"Debug: Failed to cleanup storage file {file_path}: {cleanup_res['error']['message']}")
                else:
                    print(f"Debug: Successfully cleaned up storage file {file_path}.")
            except Exception as cleanup_e:
                print(f"Debug: Unexpected error during storage cleanup: {cleanup_e}")
            return None

        if not hasattr(response, 'data') or not response.data:
            st.warning("Signature uploaded, but database record not returned in response.")
            return doc_data

        return response.data[0]
    except Exception as e:
        st.error(f"An unexpected error occurred during signature upload: {str(e)}")
        print(e)
        return None

def get_user_signatures(user_id):
    """
    Get all signatures for a user
    
    Args:
        user_id: The user's ID
    
    Returns:
        List of signature records or empty list if none found
    """
    try:
        session = supabase.auth.get_session()
        if not session or not session.user or session.user.id != user_id:
            handle_auth_failure("Cannot fetch signatures without a valid session.")
            return []

        response = supabase.table("user_signatures").select("*").eq("user_id", user_id).execute()

        if hasattr(response, 'error') and response.error:
            st.error(f"Failed to fetch signatures: {response.error.message}")
            return []

        if not hasattr(response, 'data') or not response.data:
            return []

        return response.data
    except Exception as e:
        st.error(f"An unexpected error occurred while fetching signatures: {str(e)}")
        return []

def delete_signature(doc_id, user_id, file_path):
    """
    Delete a signature from storage and database
    
    Args:
        doc_id: The document ID in the database
        user_id: The user's ID
        file_path: The file path in storage
    
    Returns:
        True if successful, False otherwise
    """
    try:
        session = supabase.auth.get_session()
        if not session or not session.user or session.user.id != user_id:
            handle_auth_failure("Authentication mismatch for signature deletion.")
            return False

        print(f"Debug: Attempting to delete storage file: {file_path}")
        storage_res = supabase.storage.from_("user-signatures").remove([file_path])

        if isinstance(storage_res, dict) and storage_res.get('error'):
            st.error(f"Failed to delete signature from storage: {storage_res['error']['message']}")
            return False
        print(f"Debug: Storage file {file_path} deleted successfully.")

        print(f"Debug: Attempting to delete DB record for doc_id: {doc_id}")
        response = supabase.table("user_signatures").delete().eq("doc_id", doc_id).eq("user_id", user_id).execute()

        if hasattr(response, 'error') and response.error:
            st.error(f"Failed to delete signature record: {response.error.message}")
            return False

        st.success("Signature deleted!")
        return True
    except Exception as e:
        st.error(f"An unexpected error occurred during signature deletion: {str(e)}")
        return False