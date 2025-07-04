"""Allows user to change their password if they wish to"""
import streamlit as st
from auth_utils import change_password

def settings_page():
    st.title("Account Settings")
    st.write("Manage your account settings here.")

    st.subheader("Change Password")
    new_password = st.text_input("New Password", type="password", help="Enter your new password.")
    confirm_password = st.text_input("Confirm New Password", type="password", help="Confirm your new password.")

    if st.button("Change Password"):
        if new_password and confirm_password:
            if new_password == confirm_password:
                change_password(new_password)
            else:
                st.error("Passwords don't match!")
        else:
            st.warning("Please enter and confirm the new password.")
