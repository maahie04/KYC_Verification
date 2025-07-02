# KYC Verification System

A Streamlit app prototype for a KYC (Know Your Customer) verification system.

# Pre-requisites
   
Ensure you have streamlit, google_generativeai, streamlit_drawable_canvas, face_recognition, supabase installed. Ensure to make a .env file with your gemini api key and a .streamlit/secrets.toml to store supabase url and key.

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
