"""Utility functions for form information"""
import streamlit as st
from supabase_client import supabase, handle_auth_failure
import datetime

def create_user_profile(email, name, dob, sex, relativename, address, phone):
    try:
        session = supabase.auth.get_session()
        if not session or not session.user or session.user.email != email:
            handle_auth_failure("Authentication required to save profile.")
            return None
        dob_str = None
        if dob:
            if isinstance(dob, datetime.date):
                dob_str = dob.strftime("%Y-%m-%d")
            elif isinstance(dob, str):
                dob_str = dob
            else:
                dob_str = str(dob)

        profile_data = {
            "id": session.user.id,
            "email": str(email),
            "name": str(name),
            "dob": dob_str,
            "sex": str(sex),
            "relativename": str(relativename),
            "address": str(address),
            "phone": str(phone),
            "updated_at": datetime.datetime.now().isoformat()
        }

        response = supabase.table("user_profiles").upsert(profile_data, on_conflict="id").execute()

        if hasattr(response, 'error') and response.error:
            st.error(f"Failed to save profile: {response.error.message}")
            return None

        if not hasattr(response, 'data') or not response.data:
            print("Debug: Profile upserted successfully, but no data returned in response.")
            return profile_data

        return response.data[0]
    except Exception as e:
        st.error(f"An unexpected error occurred while saving profile: {str(e)}")
        return None

def get_user_profile(email):
    try:
        session = supabase.auth.get_session()
        if not session or not session.user or session.user.email != email:
            handle_auth_failure("Cannot fetch profile without a valid session.")
            return None

        response = supabase.table("user_profiles").select("*").eq("id", session.user.id).execute()

        if hasattr(response, 'error') and response.error:
            st.error(f"Failed to fetch profile: {response.error.message}")
            return None

        if not hasattr(response, 'data') or not response.data:
            return None

        return response.data[0]
    except Exception as e:
        st.error(f"An unexpected error occurred while fetching profile: {str(e)}")
        return None
