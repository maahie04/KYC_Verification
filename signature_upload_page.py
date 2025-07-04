"""Allows user to submit their signatures using the touchpad and a picture of their handwritten signature. This will later be compared with their ID card signatures manually for final verification."""
import streamlit as st
from streamlit_drawable_canvas import st_canvas
from signature_utils import upload_signature, get_user_signatures

def signature_upload_page():
    # Check if live verification is done
    if not st.session_state.get('live_verified', False):
        st.warning("Please complete live verification first!")
        st.stop()
    
    st.title("Signature Upload")
    
    # Initialize session state variables if they don't exist
    if 'signatures' not in st.session_state:
        st.session_state.signatures = []
    
    # Get existing signatures
    user_id = st.session_state.supabase_session.user.id
    existing_signatures = get_user_signatures(user_id)
    st.session_state.signatures = existing_signatures
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Upload Your Written Signature")
        uploaded_file = st.file_uploader("Upload signature image", type=["png", "jpg", "jpeg"], key="written_uploader")
        
        if uploaded_file is not None:
            # Check if written signature already exists
            has_written = any(sig['document_type'] == 'written_signature' for sig in st.session_state.signatures)
            
            if has_written:
                st.warning("You've already uploaded a written signature")
            else:
                # Upload to Supabase
                result = upload_signature(
                    user_id=user_id,
                    document_type="written_signature",
                    file=uploaded_file
                )
                
                if result:
                    st.session_state.signatures.append(result)
                    st.image(uploaded_file, width=200)
                    st.success("Written signature uploaded successfully!")
    
    with col2:
        st.subheader("Draw Your Signature")
        # Create a canvas component
        canvas_result = st_canvas(
            fill_color="rgba(255, 165, 0, 0.3)",
            stroke_width=3,
            stroke_color="#000000",
            background_color="#ffffff",
            height=150,
            width=300,
            drawing_mode="freedraw",
            key="canvas",
        )
        
        if canvas_result.image_data is not None:
            if st.button("Save Drawn Signature"):
                # Check if drawn signature already exists
                has_drawn = any(sig['document_type'] == 'drawn_signature' for sig in st.session_state.signatures)
                
                if has_drawn:
                    st.warning("You've already saved a drawn signature")
                else:
                    # Upload drawn signature to Supabase
                    result = upload_signature(
                        user_id=user_id,
                        document_type="drawn_signature",
                        file=canvas_result.image_data,
                        is_drawn=True
                    )
                    
                    if result:
                        st.session_state.signatures.append(result)
                        st.image(canvas_result.image_data, width=200)
                        st.success("Drawn signature saved successfully!")
    
    # Check if both signatures are provided
    has_written = any(sig['document_type'] == 'written_signature' for sig in st.session_state.signatures)
    has_drawn = any(sig['document_type'] == 'drawn_signature' for sig in st.session_state.signatures)
    
    if has_written and has_drawn:
        st.session_state.signature_uploaded = True
        st.success("Both signatures received! You can now view your verification report.")
    
    if st.session_state.get('signature_uploaded', False):
        st.write("Verification complete! You can now view your verification report.")
