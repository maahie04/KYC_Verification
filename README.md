# KYC Verification System

A Streamlit app prototype for a KYC (Know Your Customer) verification system. [The system uses `python==3.11.8`]

# Pre-requisites
   
1. Ensure you have `streamlit`, `google_generativeai`, `streamlit_drawable_canvas`, `face_recognition`, `supabase` installed.
```bash
pip install streamlit, google_generativeai, streamlit_drawable_canvas, face_recognition, supabase
```
2.  Ensure to make a `.env` file with your gemini api key and a `.streamlit/secrets.toml` to store supabase url and key.

Make the `.env` file as:
```bash
GOOGLE_API_KEY=<Your API key>
```
Make the `.streamlit/secrets.toml` as:
```bash
[supabase]
url = "<Your supabase URL>"
key = "<Your supabase KEY>"
```

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
![image](https://github.com/user-attachments/assets/cb2ae2e5-8098-4929-867b-fd51656fcf58)

## Document Upload
![image](https://github.com/user-attachments/assets/aca08bcb-0fb6-4684-81d0-0399985e7e6b)

## Document Verification
![Untitled design](https://github.com/user-attachments/assets/c3a6a70b-21c9-4b3b-87b5-e3dfd9b3eaf0)

## Live Verification
![Untitled design (1)](https://github.com/user-attachments/assets/bc13ad6b-1cf8-408b-95ca-46ba0d75ec6f)

## Signature Upload
![Untitled design (2)](https://github.com/user-attachments/assets/0db8e735-fcd9-47e0-9d5f-fc709b92ccaa)

## Report Generation
![Untitled design (3)](https://github.com/user-attachments/assets/ccbb5845-f964-476f-a004-0fc23f0b4ce8)

## Report Example
![image](https://github.com/user-attachments/assets/e7323fbd-fd3f-4663-8216-842f65b078af)



