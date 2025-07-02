# KYC Verification System

A Streamlit app prototype for a KYC (Know Your Customer) verification system.

# Pre-requisites
   
Ensure you have `streamlit`, `google_generativeai`, `streamlit_drawable_canvas`, `face_recognition`, `supabase` installed. Ensure to make a `.env` file with your gemini api key and a `.streamlit/secrets.toml` to store supabase url and key.

## Local Testing

The `local_test` folder allows you to test the verification logic locally on your PC.

### How to test locally:
1. Place your test images in the `local_test` folder
2. Run the pipeline script:
   ```bash
   python local_test/pipeline.py

# Testing the App
To run the app and see how it works, run this command:
```bash
streamlit run app.py
```

# Demo

## Login/Sign-Up page
![image](https://github.com/user-attachments/assets/e2775e0a-a390-4b21-a733-5c8d6a1aaed2)

## User Profile
![image](https://github.com/user-attachments/assets/28c4d8eb-cab6-42ee-9c74-f8eca6153297)

## Document Upload
![image](https://github.com/user-attachments/assets/aca08bcb-0fb6-4684-81d0-0399985e7e6b)


