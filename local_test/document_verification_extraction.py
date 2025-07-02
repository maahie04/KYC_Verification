import json
import os
from datetime import datetime,timedelta
import google.generativeai as genai
from PIL import Image
from dotenv import load_dotenv
load_dotenv(".env")
def configuration():
    fetched_api_key = os.getenv("GOOGLE_API_KEY")
    genai.configure(api_key=fetched_api_key)


def classify_indian_doc(image_path):
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = """
        Classify this Indian document into one of these types:
        - Indian Passport (alphanumeric on the top right, below "Passport no.", "Republic of India" on top, two images of holder)
        - Indian PAN Card (10-digit alphanumeric, "INCOME TAX DEPARTMENT" top left, QR code/ metallic square on the right)
        - Occluded Indian Aadhar Card (4 digit number with the first 8 digits occluded located above the VID number, UDAI logo, horizontal line extending below the VID number)
        - Indian Aadhaar Card (12-digit located above VID number, UIDAI logo, horizontal line extending below the VID number)
        - Back Aadhaar Card (12 digit number, QR code on the right with address to the left, UDAI logo, horizontal line extending at the bottom)
        - Indian Driving License (alphanumeric below the Issued by state RTO, picture located to the right side, top right sybol for state)
        - Indian Voter ID (vertical, Election Comission of India on top, UID after Bar code)

        Return ONLY the document type (e.g., "Indian Passport"), Name of Holder, Date of birth(if available) and the associated alphanumeric.Each in a different line. No explanations.
        """
        img = Image.open(image_path)
        response = model.generate_content([prompt, img])
        
        lines = [line.strip() for line in response.text.split('\n') if line.strip()]
        doc_data = {
            "document_type": lines[0] if len(lines) > 0 else "",
            "name": lines[1] if len(lines) > 1 else "",
            "date_of_birth": lines[2] if len(lines) > 2 else "",
            "document_number": lines[3] if len(lines) > 3 else ""
        }
        return doc_data
        
    except Exception as e:
        return {"error": str(e)}

def additional_info(image_path, classification_result):
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        doc_type = classification_result.get("document_type", "")

        prompt = f"""
        Analyze this {doc_type} document image and extract the following information:
        """
        
        if "PAN" in doc_type:
            prompt += "Parent's Name (second name from top)"
        elif "Passport" in doc_type:
            prompt += "Nationality, Sex, Place of Birth, Place of Issue, Date of Issue, Date of Expiry"
        elif "Aadhaar" in doc_type:
            prompt += "Gender, Mobile Number (if present, will only be written in front of the words: 'Phone no.:'), Address (if present)"
        elif "Driving" in doc_type:
            prompt += "Issue Date, Validity, Father/Mother/Spouse name, Blood Group(eg A+, B+, A-, B-, AB+, O, etc.), Organ Donor status, Address"
        elif "Voter" in doc_type:
            prompt += "Parent's Name"
            
        prompt += """
        - Return ONLY the information values, each on a new line
        - If any field is not available or incomplete, skip it
        - No labels, headings, or explanations
        """
        
        img = Image.open(image_path)
        response = model.generate_content([prompt, img])
        
        lines = [line.strip() for line in response.text.split('\n') if line.strip()]
        additional_data = {}
        
        if "PAN" in doc_type:
            if len(lines) > 0:
                additional_data["parent_name"] = lines[0]
        elif "Passport" in doc_type:
            if len(lines) > 0: additional_data["nationality"] = lines[0]
            if len(lines) > 1: additional_data["sex"] = lines[1]
            if len(lines) > 2: additional_data["place_of_birth"] = lines[2]
            if len(lines) > 3: additional_data["place_of_issue"] = lines[3]
            if len(lines) > 4: additional_data["date_of_issue"] = lines[4]
            if len(lines) > 5: additional_data["date_of_expiry"] = lines[5]
        elif "Aadhaar" in doc_type:
            if len(lines) > 0: additional_data["gender"] = lines[0]
            if len(lines) > 1: additional_data["mobile_number"] = lines[1]
            if len(lines) > 2: additional_data["address"] = " ".join(lines[2:])
        elif "Driving" in doc_type:
            if len(lines) > 0: additional_data["issue_date"] = lines[0]
            if len(lines) > 1: additional_data["validity"] = lines[1]
            if len(lines) > 2: additional_data["relation"] = lines[2]
            if len(lines) > 3: additional_data["address"] = " ".join(lines[3:5])
            if len(lines) > 5: additional_data["blood_group"] = lines[5]
            if len(lines) > 6: additional_data["organ_donor"] = lines[6]
        elif "Voter" in doc_type:
            if len(lines) > 0: additional_data["parent_name"] = lines[0]
            
        return additional_data
        
    except Exception as e:
        return {"error": str(e)}

def extract_expiry_date(additional_info):
    """Use the expiry date as found in the additional information and check weather it is close to expiry or not"""
    try:
        expiry_date_str = None
        if "date_of_expiry" in additional_info:
            expiry_date_str = additional_info["date_of_expiry"]
        elif "validity" in additional_info:
            expiry_date_str = additional_info["validity"]
        
        if not expiry_date_str:
            return None, None  

        for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y"):
            try:
                expiry_date = datetime.strptime(expiry_date_str, fmt).date()
                break
            except ValueError:
                continue
        else:
            return None, None 

        today = datetime.now().date()
        six_months_later = today + timedelta(days=180) 

        is_near_expiry = expiry_date <= six_months_later
        return expiry_date.strftime("%Y-%m-%d"), is_near_expiry

    except Exception as e:
        print(f"Error processing expiry date: {str(e)}")
        return None, None
    
def save_to_json(data, filename='document_data.json'):
    try:
        if os.path.exists(filename) and os.path.getsize(filename) > 0:
            with open(filename, 'r') as f:
                existing_data = json.load(f)
            if isinstance(existing_data, list):
                existing_data.append(data)
            else:
                existing_data = [existing_data, data]
        else:
            existing_data = [data]
        
        with open(filename, 'w') as f:
            json.dump(existing_data, f, indent=2)
            
        print(f"Data successfully saved to {filename}")
    except Exception as e:
        print(f"Error saving to JSON: {str(e)}")

def initialization(img_path):
    configuration()
    image_path=img_path
    classification_result = classify_indian_doc(image_path)
    print("Classification Result:")
    print(json.dumps(classification_result, indent=2))
    additional_result = additional_info(image_path, classification_result)
    print("\nAdditional Information:")
    print(json.dumps(additional_result, indent=2))

    expiry_date, is_near_expiry = extract_expiry_date(additional_result)
    print(f"\nExpiry Date: {expiry_date}")
    print(f"Needs Renewal (<6 months): {is_near_expiry}")

    final_result = {
        "timestamp": datetime.now().isoformat(),
        "document_information": classification_result,
        "additional_information": additional_result,
        "expiry_info": {
            "expiry_date": expiry_date,
            "needs_renewal_soon": is_near_expiry
        } if expiry_date else None
    }
    save_to_json(final_result)

image_path = "IMG_20250606_102358.jpg"

classification_result = classify_indian_doc(image_path)
print("Classification Result:")
print(json.dumps(classification_result, indent=2))

additional_result = additional_info(image_path, classification_result)
print("\nAdditional Information:")
print(json.dumps(additional_result, indent=2))

expiry_date, is_near_expiry = extract_expiry_date(additional_result)
print(f"\nExpiry Date: {expiry_date}")
print(f"Needs Renewal (<6 months): {is_near_expiry}")

final_result = {
    "timestamp": datetime.now().isoformat(),
    "document_information": classification_result,
    "additional_information": additional_result,
    "expiry_info": {
        "expiry_date": expiry_date,
        "needs_renewal_soon": is_near_expiry
    } if expiry_date else None
}

save_to_json(final_result)

def initialization(img_path):
    configuration()
    image_path=img_path
    classification_result = classify_indian_doc(image_path)
    print("Classification Result:")
    print(json.dumps(classification_result, indent=2))
    additional_result = additional_info(image_path, classification_result)
    print("\nAdditional Information:")
    print(json.dumps(additional_result, indent=2))

    expiry_date, is_near_expiry = extract_expiry_date(additional_result)
    print(f"\nExpiry Date: {expiry_date}")
    print(f"Needs Renewal (<6 months): {is_near_expiry}")

    final_result = {
        "timestamp": datetime.now().isoformat(),
        "document_information": classification_result,
        "additional_information": additional_result,
        "expiry_info": {
            "expiry_date": expiry_date,
            "needs_renewal_soon": is_near_expiry
        } if expiry_date else None
    }
    save_to_json(final_result)
