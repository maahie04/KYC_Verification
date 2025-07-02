import streamlit as st
import datetime
from profile_utils import get_user_profile, create_user_profile
from photo_utils import upload_picture
from supabase_client import supabase

def get_profile_photo_url(user_id):
    try:
        photo_data = supabase.table("user_pictures").select("*").eq(
            "user_id", user_id
        ).eq("document_type", "profile").order("created_at", desc=True).limit(1).execute()
       
        if photo_data.data:
            return supabase.storage.from_("user-pictures").get_public_url(photo_data.data[0]['file_path'])
    except Exception as e:
        st.error(f"Couldn't load profile photo: {str(e)}")
    return None

def profile_page():
    st.title("User Profile")
    st.write("Update your personal information.")

    profile = get_user_profile(st.session_state.user_email)
    profile_data = profile or {}

    current_photo_url = get_profile_photo_url(st.session_state.supabase_session.user.id)

    with st.form("profile_form"):
        name = st.text_input("Name", value=profile_data.get("name", ""), key="profile_name")

        dob_value = profile_data.get("dob")
        if isinstance(dob_value, str):
            try:
                dob_date = datetime.datetime.strptime(dob_value, "%Y-%m-%d").date()
            except (ValueError, TypeError):
                dob_date = None
        elif isinstance(dob_value, datetime.date):
            dob_date = dob_value
        else:
            dob_date = None

        dob = st.date_input(
            "Date of Birth",
            value=dob_date,
            min_value=datetime.date(1900, 1, 1),
            max_value=datetime.date.today(),
            help="Select your date of birth.",
            key="profile_dob"
        )

        sex_options = ["Male", "Female", "Prefer not to say"]
        current_sex = profile_data.get("sex", "")
        sex = st.selectbox(
            "Sex", 
            sex_options, 
            index=sex_options.index(current_sex) if current_sex in sex_options else 0, 
            help="Select your sex.",
            key="profile_sex"
        )

        relativename = st.text_input(
            "Name of Father/Mother/Spouse", 
            value=profile_data.get("relativename", ""), 
            help="Enter the name of a relative.",
            key="profile_relativename"
        )

        address = st.text_input(
            "Address", 
            value=profile_data.get("address", ""), 
            help="Enter your current address.",
            key="profile_address"
        )

        phone_value = profile_data.get("phone", "")
        phone_int_value = 0
        if isinstance(phone_value, (int, float)):
            phone_int_value = int(phone_value)
        elif isinstance(phone_value, str) and phone_value.isdigit():
            phone_int_value = int(phone_value)

        phone_default = max(1000000000, min(9999999999, phone_int_value if phone_int_value >= 1000000000 else 1000000000))

        phone = st.number_input(
            "Phone number",
            min_value=1000000000,
            max_value=9999999999,
            value=phone_default,
            format="%d",
            help="Enter your 10-digit phone number.",
            key="profile_phone"
        )
        
        st.subheader("Profile Photo")
        profile_photo = st.file_uploader(
            "Upload a profile photo",
            type=["jpg", "jpeg", "png"],
            accept_multiple_files=False,
            help="Upload a clear photo of yourself for identification purposes.",
            key="profile_photo_upload"
        )

        if current_photo_url:
            st.image(current_photo_url, caption="Current Profile Photo", width=200) #If photo already uploaded then display

        submitted = st.form_submit_button("Save Profile")

        if submitted:
            required_fields = [name, dob, sex, relativename, address, phone]
            if all(required_fields):
                saved_profile = create_user_profile(
                    st.session_state.user_email, 
                    name, 
                    dob, 
                    sex, 
                    relativename, 
                    address, 
                    str(phone)
                )

                if profile_photo is not None:
                    user_id = st.session_state.supabase_session.user.id
                    upload_result = upload_picture(
                        user_id=user_id,
                        document_type="profile",
                        file=profile_photo
                    )
                    
                    if upload_result:
                        st.success("Profile photo uploaded successfully!")
                        new_photo_url = supabase.storage.from_("user-pictures").get_public_url(upload_result['file_path'])
                        st.image(new_photo_url, caption="Your new profile photo", width=200)
                    else:
                        st.error("Failed to upload profile photo")

                if saved_profile:
                    st.session_state.profile_complete = True
                    st.success("Profile saved successfully!")
                    st.rerun()
            else:
                st.error("Please fill in all required fields before saving")
                st.session_state.profile_complete = False

    if not st.session_state.get('profile_complete', False):
        required_fields = [
            profile_data.get("name"),
            profile_data.get("dob"),
            profile_data.get("sex"),
            profile_data.get("relativename"),
            profile_data.get("address"),
            profile_data.get("phone")
        ]
        if all(required_fields):
            st.session_state.profile_complete = True
            st.rerun()  