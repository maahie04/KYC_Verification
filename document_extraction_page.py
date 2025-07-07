"""Extracts information and faces from the documents, saves the faces in supabase storage and the extracted information in the session state"""
import streamlit as st
from document_information import configuration, extract_document_details
from supabase_client import supabase
import os
import tempfile
from datetime import datetime
from document_utils import get_user_documents
from face_extraction import faceextractor
from photo_utils import upload_picture
from io import BytesIO
from profile_utils import get_user_profile
from verification import verify_doc
def document_extraction_page():
    configuration()
    if not st.session_state.get('documents_uploaded', False):
        st.warning("Please upload your documents first!")
        st.stop()
   
    st.title("Document Verification")
   
    user_id = st.session_state.supabase_session.user.id
    existing_docs = get_user_documents(user_id)
    verification_status = True  
    
    if not existing_docs:
        st.error("No documents found for extraction. Please upload documents first.")
        st.stop()
   
    if st.button("Verify All Documents"):
        all_extracted_data = {}
        extracted_faces = [] 
        verification_results = {}  
        existing_face_types = set()  
        error_messages = []  # To collect all error messages
       
        with st.spinner("Extracting and verifying all documents..."):
            progress_bar = st.progress(0)
            total_docs = len(existing_docs)
           
            for i, doc in enumerate(existing_docs):
                try:
                    progress_bar.progress((i + 1) / total_docs)
                   
                    file_path = doc['file_path']
                    file_content = supabase.storage.from_("user-documents").download(file_path)
                   
                    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file_path)[1]) as temp_file:
                        temp_file.write(file_content)
                        temp_file_path = temp_file.name
                   
                    extracted_data = extract_document_details(temp_file_path)
                    
                    doc_type = doc['document_type']
                    
                    existing_faces = supabase.table('user_pictures').select('*').eq('user_id', user_id).eq('document_type', doc_type).execute()
                    
                    if not existing_faces.data:  
                        faces = faceextractor(temp_file_path)
                        if faces:
                            extracted_faces.append({
                                'type': doc_type,
                                'data': faces[0]  
                            })
                            existing_face_types.add(doc_type)
                    
                    final_result = {
                        "timestamp": datetime.now().isoformat(),
                        "document_data": extracted_data if extracted_data else {},
                        "expiry_info": extracted_data.get("expiry_info", {
                            "expiry_date": None,
                            "is_near_expiry": False
                        }) if extracted_data else {
                            "expiry_date": None,
                            "is_near_expiry": False
                        }
                    }
                    
                    profile = get_user_profile(st.session_state.user_email)
                    validity = "ERROR: No extracted data" if not extracted_data else verify_doc({
                        "document_info": {
                            "website_document_type":doc_type,
                            "document_type": extracted_data.get("document_type"),
                            "document_number": extracted_data.get("document_number"),
                            "name": extracted_data.get("name"),
                            "date_of_birth": extracted_data.get("dob")
                        },
                        "additional_info": {
                            "sex": extracted_data.get("sex"),
                            "relative_name": extracted_data.get("relative_name"),
                            "address": extracted_data.get("address"),
                            "phone": extracted_data.get("phone")
                        },
                        "expiry_info": final_result["expiry_info"]
                    }, profile)

                    verification_results[doc_type] = validity
                    if validity and "INVALID" in validity:
                        verification_status = False
                        error_messages.append(f"{doc_type}: {validity}")
                    
                    all_extracted_data[doc_type] = final_result
                    
                    os.unlink(temp_file_path)
                
                except Exception as e:
                    st.error(f"Error processing {doc['document_type']}: {str(e)}")
                    verification_status = False
                    verification_results[doc['document_type']] = f"ERROR: {str(e)}"
                    error_messages.append(f"{doc['document_type']}: {str(e)}")
                    continue
                
        if extracted_faces:
            with st.spinner("Uploading extracted faces..."):
                for face_info in extracted_faces:
                    try:
                        face_bytes = face_info['data']
                        doc_type = face_info['type']
                        
                        existing_faces = supabase.table('user_pictures').select('*').eq('user_id', user_id).eq('document_type', doc_type).execute()
                        if existing_faces.data:
                            st.warning(f"Skipping face upload for {doc_type} - already exists in database")
                            continue
                            
                        face_file = BytesIO(face_bytes)
                        face_file.name = f"face_{doc_type.lower()}_{datetime.now().strftime('%Y%m%d')}.jpg"
                        
                        class SimpleUploadedFile:
                            def __init__(self, file, name, content_type):
                                self.file = file
                                self.name = name
                                self.type = content_type
                            
                            def getvalue(self):
                                return self.file.getvalue()
                        
                        uploaded_file = SimpleUploadedFile(
                            file=face_file,
                            name=face_file.name,
                            content_type="image/jpeg"
                        )
                        
                        upload_result = upload_picture(
                            user_id=user_id,
                            document_type=doc_type,
                            file=uploaded_file
                        )
                        
                        if not upload_result:
                            error_msg = f"Failed to upload face image for {doc_type}"
                            st.error(error_msg)
                            error_messages.append(error_msg)
                        else:
                            st.success(f"Successfully uploaded face image for {doc_type}")
                    
                    except Exception as e:
                        error_msg = f"Failed to upload face image for {doc_type}: {str(e)}"
                        st.error(error_msg)
                        error_messages.append(error_msg)
                        continue
        
        st.session_state.extracted_data = all_extracted_data
        st.session_state.verification_results = verification_results
        st.session_state.verified = verification_status
        st.session_state.error_messages = error_messages  # Store errors in session state
        
        st.subheader("Document Verification Results")
        for doc_type, data in st.session_state.extracted_data.items():
            verification_result = st.session_state.verification_results.get(doc_type, "UNKNOWN")
            doc_data = data.get('document_data', {})
            expiry_info = data.get('expiry_info', {})
            
            with st.expander(f"{doc_type} Details", expanded=True):
                if verification_result and "INVALID" in verification_result:
                    st.error("❌ Verification Failed")
                elif verification_result and "VALID" in verification_result:
                    st.success("✅ Verification Passed")
                else:
                    st.warning("⚠️ Verification Status Unknown")
                
                col1, col2 = st.columns(2)
               
                with col1:
                    st.subheader("Basic Information")
                    st.write(f"**Document Type:** {doc_data.get('document_type', 'N/A')}")
                    st.write(f"**Name:** {doc_data.get('name', 'N/A')}")
                    st.write(f"**Document Number:** {doc_data.get('document_number', 'N/A')}")
                    st.write(f"**Date of Birth:** {doc_data.get('dob', 'N/A')}")
               
                with col2:
                    st.subheader("Validity")
                    status = "⚠️ Expiring Soon" if expiry_info.get('is_near_expiry', False) else "✅ Valid"
                    st.write(f"**Expiry Date:** {expiry_info.get('expiry_date', 'N/A')}")
                    st.write(f"**Status:** {status}")
                
                st.subheader("Verification Details")
                st.write(f"**Result:** {verification_result}")
               
                st.subheader("Additional Information")
                st.write(f"**Gender:** {doc_data.get('sex', 'N/A')}")
                st.write(f"**Relative Name:** {doc_data.get('relative_name', 'N/A')}")
                st.write(f"**Address:** {doc_data.get('address', 'N/A')}")
                st.write(f"**Phone:** {doc_data.get('phone', 'N/A')}")
           
            st.markdown("---")
       
        if st.session_state.verified:
            st.success("✅ All documents verified successfully!")
        else:
            st.error("❌ Some documents failed verification")
            
            # Display consolidated error list
            st.subheader("Verification Issues Summary")
            with st.expander("View all errors", expanded=True):
                for error in st.session_state.error_messages:
                    st.error(error)
            
            if st.button("Try Again"):
                st.experimental_rerun()
            
        st.subheader("Verification Summary")
       
        names = set()
        for data in st.session_state.extracted_data.values():
            doc_data = data.get('document_data', {})
            name = doc_data.get('name')
            if name and isinstance(name, str): 
                names.add(name.strip().lower())
       
        cols = st.columns(3)
        with cols[0]:
            st.metric("Documents Processed", len(existing_docs))
       
        with cols[1]:
            expiring_count = sum(1 for data in st.session_state.extracted_data.values()
                               if data.get('expiry_info', {}).get('is_near_expiry', False))
            st.metric("Expiring Soon", expiring_count)
       
        with cols[2]:
            name_status = "✅ Consistent" if len(names) <= 1 else "⚠️ Inconsistent"
            st.metric("Name Verification", name_status)
           
            if len(names) > 1:
                st.warning("Different names found across documents:")
                for name in names:
                    st.write(f"- {name.title()}")
