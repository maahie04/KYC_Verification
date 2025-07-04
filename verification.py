"""Function which compares user entered information with extracted information from the ID cards and verifies if user is the same individual or not."""
import google.generativeai as genai
import json
import os
from dotenv import load_dotenv
load_dotenv(".env")
def configuration():
    fetched_api_key = os.getenv("GOOGLE_API_KEY")
    genai.configure(api_key=fetched_api_key)

def verify_doc(doc_data, user_profile):
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        doc_str = json.dumps(doc_data, indent=2)
        profile_str = json.dumps(user_profile, indent=2)
        
        prompt = """
You are an identity verification system. Compare the document information with the user profile 
and determine if they belong to the same person. Follow these rules:
0. Website doucment type should match document type.

1. For Back Aadhar Card name will never be present so don't check name field, return "VALID" if the address matches, else return invalid. Don't check for other fields. 

2. For other documents, follow these guidelines:
   - Required fields that must match (if present in both):
     * Name (allow minor spelling variations)
     * Document number (must be valid format for document type)
   - Partially optional(can be missing but if present must exactly match):
     * Date of birth
   - Optional fields (can be missing or partially match):
     * Address
     * Phone number
     * Relative name
     * Gender

3. Evaluation rules:
   - If required fields are missing from document: "INVALID: Missing [field_name]"
   - If required fields don't match: "INVALID: [field_name] mismatch"
   - If optional fields are missing: Ignore them in verification
   - If optional fields partially match: Consider acceptable

4. Return exactly one of these responses:
   - "VALID" if all present required information matches
   - "VALID with minor discrepancies: [explanation]" if:
     * Only optional fields are missing/mismatched
     * Differences in required fields are explainable (like nickname vs full name)
   - "INVALID: [reason]" if required information doesn't match

5. Acceptable variations:
   - Shortened names (William vs Bill)
   - Initials vs full names
   - Address line order variations
   - Missing middle names
   - Missing optional fields (address, phone, etc.)
   - Partial address matches (building name matches but flat number missing)

DOCUMENT DATA:
{doc_str}

USER PROFILE:
{profile_str}

Important: 
- Focus on matching what's present in both documents
- Don't penalize for missing optional fields
- Be lenient with address/phone formatting

Your verification response must begin with either "VALID" or "INVALID":
"""
        
        response = model.generate_content(prompt.format(doc_str=doc_str, profile_str=profile_str))
        result = response.text.strip()
        if not (result.startswith("VALID") or result.startswith("INVALID")):
            return "VALID" if "valid" in result.lower() else "INVALID: Could not determine"
        return result
        
    except Exception as e:
        return f"ERROR: {str(e)}"
