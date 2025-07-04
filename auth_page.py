"""The sign-up/sign-in page, deals with creation or logging into your account, uses the auth_utils.py functions"""
import streamlit as st
from auth_utils import sign_up, sign_in
def auth_screen():
    st.title("KYC Verification App")
    st.write("Please log in or sign up to continue.")

    option = st.selectbox("Choose an action:", ['Login', 'Sign Up'])
    email = st.text_input("Email")
    password = st.text_input("Password", type='password')

    if option == 'Sign Up' and st.button("Register"):
        if email and password:
            sign_up(email, password)
        else:
            st.warning("Please enter both email and password.")

    if option == 'Login' and st.button('Login'):
        if email and password:
            sign_in(email, password)
        else:
            st.warning("Please enter both email and password.")
