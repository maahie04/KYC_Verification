import streamlit as st
from profile_page import profile_page
from document_extraction_page import document_extraction_page
from live_verification_page import live_verification_page
from signature_upload_page import signature_upload_page
from verification_report_page import verification_report_page
from auth_page import auth_screen
from documents_page import documents_page
from settings_page import settings_page
from supabase_client import supabase, handle_auth_failure
from auth_utils import sign_out
import datetime

def initialize_session_state():
    """Initialize all required session state variables"""
    defaults = {
        'user_email': None,
        'user_name': None,
        'user_phone': None,
        'supabase_session': None,
        'page': 'auth',
        'current_page': 'Profile Details',
        'verified': False,
        'live_verified': False,
        'profile_complete': False,
        'documents_uploaded': False,
        'signature_uploaded': False,
        'extracted_data': None,
        'signatures': [],
        'last_activity': datetime.datetime.now()
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def verify_session():
    """Verify and maintain the Supabase session"""
    if st.session_state.supabase_session:
        try:
            # Check session expiration
            if hasattr(st.session_state.supabase_session, 'expires_at'):
                if datetime.datetime.now().timestamp() > st.session_state.supabase_session.expires_at:
                    handle_auth_failure("Session expired. Please log in again.")
                    return False

            # Refresh session if needed
            access_token = st.session_state.supabase_session.access_token
            refresh_token = st.session_state.supabase_session.refresh_token
            
            if access_token and refresh_token:
                set_resp = supabase.auth.set_session(access_token, refresh_token)
                
                if hasattr(set_resp, 'session') and set_resp.session:
                    st.session_state.supabase_session = set_resp.session
                    if hasattr(set_resp.session, 'user') and set_resp.session.user:
                        st.session_state.user_email = set_resp.session.user.email
                    return True
                elif hasattr(set_resp, 'error') and set_resp.error:
                    print(f"Session error: {set_resp.error.message}")
                    handle_auth_failure("Session error. Please log in again.")
                else:
                    print("Unexpected session response")
                    handle_auth_failure("Session error. Please log in again.")
            else:
                print("Missing session tokens")
                handle_auth_failure("Invalid session. Please log in again.")
        except Exception as e:
            print(f"Session verification error: {str(e)}")
            handle_auth_failure(f"Session error: {str(e)}")
    
    return False

def get_available_pages():
    """Determine which pages should be available based on verification progress"""
    available_pages = {
        "Profile Details": profile_page,
        "Settings": settings_page,
        "Verification Report": verification_report_page
    }
    
    # Progressive disclosure of pages based on completion status
    if st.session_state.profile_complete:
        available_pages["Document Upload"] = documents_page
        
    if st.session_state.documents_uploaded:
        available_pages["Document Verification"] = document_extraction_page
        
    if st.session_state.verified:
        available_pages["Live Verification"] = live_verification_page
        
    if st.session_state.live_verified:
        available_pages["Signature Upload"] = signature_upload_page
    
    return available_pages

def main():
    """The main page routing to the different pages"""
    st.set_page_config(
        page_title="Identity Verification System", 
        layout="wide",
        page_icon="🔒"
    )
    initialize_session_state()
    if st.session_state.supabase_session and not verify_session():
        return
    if not st.session_state.user_email or not st.session_state.supabase_session:
        auth_screen()
        return
    st.sidebar.title("Welcome!")
    st.sidebar.markdown(f"*{st.session_state.user_email}*")
    available_pages = get_available_pages()
    current_page = st.session_state.current_page
    if current_page not in available_pages:
        current_page = "Profile Details"
        st.session_state.current_page = current_page
    page_names = list(available_pages.keys())
    current_index = page_names.index(current_page) if current_page in page_names else 0
    
    selection = st.sidebar.radio("Navigation", page_names, index=current_index)

    if selection != st.session_state.current_page:
        st.session_state.current_page = selection
        st.rerun()
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Verification Progress")
    
    verification_steps = [
        ("Profile", st.session_state.profile_complete),
        ("Documents", st.session_state.documents_uploaded),
        ("Verification", st.session_state.verified),
        ("Live Check", st.session_state.live_verified),
        ("Signature", st.session_state.signature_uploaded)
    ]
    
    for step, completed in verification_steps:
        status = "✅" if completed else "◻️"
        st.sidebar.markdown(f"{status} {step}")
    
    st.sidebar.markdown("---")
    if st.sidebar.button("Logout", key="logout_button"):
        sign_out()
        st.rerun()
    
    try:
        available_pages[selection]()
    except Exception as e:
        st.error(f"Error loading page: {str(e)}")
        st.stop()

if __name__ == "__main__":
    main()