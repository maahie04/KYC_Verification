import streamlit as st
import face_recognition as fr
import cv2
import time
import numpy as np
from supabase_client import supabase
from photo_utils import get_user_picture
import tempfile
import os

def load_and_encode(image_path):
    img = cv2.imread(image_path)
    img = cv2.flip(img, 1)
    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    encodings = fr.face_encodings(rgb)
    if len(encodings) == 0:
        return None
    return encodings[0]

def download_and_save_image(url, temp_dir):
    try:
        file_path = url.split('user-pictures/')[-1]
        file_content = supabase.storage.from_("user-pictures").download(file_path)

        temp_file_path = os.path.join(temp_dir, os.path.basename(file_path))
        with open(temp_file_path, 'wb') as f:
            f.write(file_content)
        
        return temp_file_path
    except Exception as e:
        st.error(f"Error downloading image: {str(e)}")
        return None

def perform_live_verification(profile_image_path, other_image_paths):

    try:
        profile_faceenc = load_and_encode(profile_image_path)
        if profile_faceenc is None:
            st.error("Could not detect face in profile image")
            return False, None
    except Exception as e:
        st.error(f"Error loading profile image: {e}")
        return False, None

    videocapture = cv2.VideoCapture(0)
    if not videocapture.isOpened():
        st.error("Could not open video capture")
        return False, None

    matches_required = 10
    successful_matches = 0
    total_time = 30
    start_time = time.time()
    frame_count = 0
    verification_results = {}

    video_placeholder = st.empty()

    for doc_type, image_path in other_image_paths.items():
        try:
            other_faceenc = load_and_encode(image_path)
            if other_faceenc is None:
                verification_results[doc_type] = "No face detected"
                continue

            ref_match = fr.compare_faces([profile_faceenc], other_faceenc)[0]
            if not ref_match:
                verification_results[doc_type] = "Reference mismatch"
                continue
        except Exception as e:
            verification_results[doc_type] = f"Error: {str(e)}"
            continue

        successful_matches = 0
        start_time = time.time()
        
        while (time.time() - start_time < total_time and 
               successful_matches < matches_required):
            ret, frame = videocapture.read()
            if not ret:
                break

            try:
                if frame_count % 3 != 0:
                    frame_count += 1
                    continue

                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                face_locations = fr.face_locations(rgb_frame)
                
                if len(face_locations) != 1:
                    status = "Ensure one face in frame" if len(face_locations) == 0 else "Multiple faces detected"
                    cv2.putText(frame, status, (50, 50), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
                    video_placeholder.image(frame, channels="BGR")
                    frame_count += 1
                    continue

                face_encoding = fr.face_encodings(rgb_frame, face_locations)[0]

                match1 = fr.compare_faces([profile_faceenc], face_encoding)[0]
                match2 = fr.compare_faces([other_faceenc], face_encoding)[0]
                dist1 = fr.face_distance([profile_faceenc], face_encoding)[0]
                dist2 = fr.face_distance([other_faceenc], face_encoding)[0]

                top, right, bottom, left = face_locations[0]
                color = (0, 255, 0) if ((dist1 <= 0.50 and dist2 <= 0.50) or (dist1 <= 0.60 and dist2 <= 0.45) or (dist1 <= 0.45 and dist2 <= 0.60)) else (0, 0, 255)
                cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
                
                status = f"Match {successful_matches+1}/{matches_required}" if ((dist1 <= 0.50 and dist2 <= 0.50) or (dist1 <= 0.60 and dist2 <= 0.45) or (dist1 <= 0.45 and dist2 <= 0.60)) else "No match"
                cv2.putText(frame, f"{status} {doc_type} D1:{dist1:.2f} D2:{dist2:.2f}", 
                           (left, top-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
                
                video_placeholder.image(frame, channels="BGR")
                
                if ((dist1 <= 0.50 and dist2 <= 0.50) or (dist1 <= 0.60 and dist2 <= 0.45) or (dist1 <= 0.45 and dist2 <= 0.60)):
                    successful_matches += 1
                
                frame_count += 1

            except Exception as e:
                st.error(f"Error processing frame: {e}")
                frame_count += 1

        verification_results[doc_type] = successful_matches >= matches_required

    videocapture.release()
    cv2.destroyAllWindows()

    overall_result = all(result == True for result in verification_results.values())
    return overall_result, verification_results

def live_verification_page():

    if not st.session_state.get('verified', False):
        st.warning("Please complete document verification first!")
        st.stop()
    
    st.title("Live Verification")
    st.subheader("Please complete the live verification process")
    
    st.info("""
    Instructions:
    1. Make sure you're in a well-lit area
    2. Position your face in the frame
    3. Ensure you are the only person on screen
    4. You'll need to match your face 10 times within 30 seconds for each document type
    """)
    
    user_id = st.session_state.supabase_session.user.id
    pictures = get_user_picture(user_id)
    
    if not pictures or len(pictures) < 2:
        st.error("At least 2 reference images are required for live verification")
        st.stop()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        image_paths = {}
        profile_image_path = None
        
        for picture in pictures:
            if 'file_path' in picture:
                image_path = download_and_save_image(picture['file_path'], temp_dir)
                if image_path:
                    doc_type = picture.get('document_type', 'unknown')
                    if doc_type.lower() == 'profile':
                        profile_image_path = image_path
                    else:
                        image_paths[doc_type] = image_path
        
        if not profile_image_path:
            st.error("Profile image not found - required for verification")
            st.stop()
        
        if not image_paths:
            st.error("No other document images found for verification")
            st.stop()
       
        if st.button("Start Live Verification"):
            with st.spinner("Verifying your identity against all document types..."):
                verification_result, detailed_results = perform_live_verification(profile_image_path, image_paths)
                st.session_state.live_verified = verification_result
                st.session_state.verification_details = detailed_results
                
                if verification_result:
                    st.success("Live verification successful for all document types!")
                else:
                    st.error("Live verification failed for some document types")
                
                # Show detailed results
                st.subheader("Verification Details")
                for doc_type, result in detailed_results.items():
                    if result == True:
                        st.success(f"✅ {doc_type}: Verified")
                    elif isinstance(result, str):
                        st.error(f"❌ {doc_type}: {result}")
                    else:
                        st.error(f"❌ {doc_type}: Failed")
    
    if st.session_state.get('live_verified', False):
        st.write("You can now proceed to signature upload")