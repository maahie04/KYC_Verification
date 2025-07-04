"""Contains the authentication utility functions which help the user to log in or sign up"""
import streamlit as st
from supabase_client import supabase, handle_auth_failure
import datetime
import uuid
import os

def sign_up(email, password):
    try:
        response = supabase.auth.sign_up({"email": email, "password": password})

        if hasattr(response, 'user') and response.user:
            if hasattr(response, 'session') and response.session:
                st.session_state.user_email = response.user.email
                st.session_state.supabase_session = response.session

                from profile_utils import create_user_profile
                created_profile = create_user_profile(response.user.email, "", None, "", "", "", "")
                if created_profile:
                    st.success('Registration successful and logged in. Profile created.')
                else:
                    st.warning('Registration successful and logged in, but failed to create initial profile. Please update your profile manually.')

                st.session_state.page = "profile"
                st.rerun()
                return response.user
            else:
                st.success('Registration successful. Please check your email to confirm your account before logging in.')
                return response.user
        elif hasattr(response, 'error') and response.error:
            st.error(f"Registration failed: {response.error.message}")
            return None
        else:
            st.error("Registration failed: Unexpected response from server.")
            return None
    except Exception as e:
        st.error(f"An unexpected error occurred during registration: {str(e)}")
        return None

def sign_in(email, password):
    try:
        response = supabase.auth.sign_in_with_password({"email": email, "password": password})

        if hasattr(response, 'user') and response.user and hasattr(response, 'session') and response.session:
            st.session_state.user_email = response.user.email
            st.session_state.supabase_session = response.session

            st.success(f"Welcome back, {email}!")
            st.session_state.page = "profile"
            st.rerun()
            return response.user
        elif hasattr(response, 'error') and response.error:
            st.error(f"Login failed: {response.error.message}")
            return None
        else:
            st.error("Login failed: Unexpected response.")
            return None
    except Exception as e:
        st.error(f"An unexpected error occurred during login: {str(e)}")
        return None

def sign_out():
    try:
        if st.session_state.supabase_session and hasattr(st.session_state.supabase_session, 'access_token') and hasattr(st.session_state.supabase_session, 'refresh_token'):
            try:
                supabase.auth.set_session(st.session_state.supabase_session.access_token, st.session_state.supabase_session.refresh_token)
            except Exception as e:
                print(f"Debug: Error setting session before sign_out: {e}")

        response = supabase.auth.sign_out()

        st.session_state.user_email = None
        st.session_state.supabase_session = None
        st.session_state.page = "auth"
        st.rerun()

        if hasattr(response, 'error') and response.error:
            print(f"Debug: Server-side logout issue: {response.error.message}")
    except Exception as e:
        st.error(f"An unexpected error occurred during logout: {str(e)}")
        st.session_state.user_email = None
        st.session_state.supabase_session = None
        st.session_state.page = "auth"
        st.rerun()

def change_password(new_password):
    try:
        session = supabase.auth.get_session()
        if not session or not session.user:
            handle_auth_failure("You must be logged in to change your password.")
            return False

        response = supabase.auth.update_user({"password": new_password})

        if hasattr(response, 'user') and response.user:
            st.success("Password updated successfully!")
            if hasattr(response, 'session') and response.session:
                st.session_state.supabase_session = response.session
            return True
        elif hasattr(response, 'error') and response.error:
            st.error(f"Password update failed: {response.error.message}")
            return False
        else:
            st.error("Password update failed: Unexpected response.")
            return False
    except Exception as e:
        st.error(f"An unexpected error occurred during password change: {str(e)}")
        return False
