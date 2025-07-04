"""Supabase configuration"""
import streamlit as st
from supabase import create_client, Client

try:
    supabase_url = st.secrets["supabase"]["url"]
    supabase_key = st.secrets["supabase"]["key"]
    supabase: Client = create_client(supabase_url, supabase_key)
except KeyError:
    st.error("Supabase credentials not found in .streamlit/secrets.toml")
    st.info("Please create a '.streamlit' folder in your app directory and add a 'secrets.toml' file with your Supabase URL and Key.")
    st.stop()
except Exception as e:
    st.error(f"Failed to initialize Supabase client: {e}")
    st.stop()

def handle_auth_failure(message="Your session has expired or is invalid. Please log in again."):
    st.error(message)
    st.session_state.user_email = None
    st.session_state.supabase_session = None
    st.session_state.page = "auth"
    st.rerun()
