"""Function used to extract information using Gen-AI, also check for expiry validity"""
import json
import os
from datetime import datetime, timedelta
import google.generativeai as genai
from PIL import Image
import os
from dotenv import load_dotenv
load_dotenv(".env")
def configuration():
    fetched_api_key = os.getenv("GOOGLE_API_KEY")
    genai.configure(api_key=fetched_api_key)

def extract_expiry_date(document_data):
    """Extract expiry date from document data and check if it's close to expiry"""
    try:
        expiry_date_str = None
        if "date_of_expiry" in document_data:
            expiry_date_str = document_data["date_of_expiry"]
        elif "validity" in document_data:
            expiry_date_str = document_data["validity"]
        
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

def extract_document_details(image_path):
    """Classify the document and extract key fields including expiry date"""
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

        Analyze this Indian document and extract the following information in JSON format:
        {
            "document_type": "",  # Classify as given above
            "document_number": "",  # The full document number
            "name": "",  # Full name of the document holder
            "dob": "",  # Date of birth in YYYY-MM-DD format
            "sex": "",  # Gender if available
            "relative_name": "",  # Father/Mother/Spouse name
            "address": "",  # Complete address
            "phone": "",  # Phone number
            "date_of_expiry": "",  # Expiry date in YYYY-MM-DD format if available
            "validity": ""  # Alternative field for expiry/validity date
        }

        Rules:
        1. Return ONLY the JSON structure with the extracted values
        2. If any field is not available in the document, set it to null
        3. For dates, always use YYYY-MM-DD format when possible
        4. Include both date_of_expiry and validity fields if found
        5. Be extremely accurate - don't hallucinate any details
        """
        
        img = Image.open(image_path)
        response = model.generate_content([prompt, img])
        
        try:
            json_str = response.text.strip().replace('```json', '').replace('```', '').strip()
            data = json.loads(json_str)
            
            required_fields = [
                "document_type", "document_number", "name", "dob", 
                "sex", "relative_name", "address", "phone",
                "date_of_expiry", "validity"
            ]
            
            for field in required_fields:
                if field not in data:
                    data[field] = None
                elif data[field] == "":
                    data[field] = None
            
            expiry_date, is_near_expiry = extract_expiry_date(data)
            data["expiry_info"] = {
                "expiry_date": expiry_date,
                "is_near_expiry": is_near_expiry
            }
            
            return data
            
        except json.JSONDecodeError:
            return {
                "document_type": None,
                "document_number": None,
                "name": None,
                "dob": None,
                "sex": None,
                "relative_name": None,
                "address": None,
                "phone": None,
                "date_of_expiry": None,
                "validity": None,
                "expiry_info": {
                    "expiry_date": None,
                    "is_near_expiry": None
                },
                "error": "Could not parse model response as JSON"
            }
            
    except Exception as e:
        return {
            "document_type": None,
            "document_number": None,
            "name": None,
            "dob": None,
            "sex": None,
            "relative_name": None,
            "address": None,
            "phone": None,
            "date_of_expiry": None,
            "validity": None,
            "expiry_info": {
                "expiry_date": None,
                "is_near_expiry": None
            },
            "error": str(e)
        }

def save_to_json(data, filename='document_data.json'):
    """Save extracted data to JSON file"""
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

def process_document(image_path):
    """Main function to process document and return structured data"""
    configuration()
    extracted_data = extract_document_details(image_path)
    
    print("Extracted Document Details:")
    print(json.dumps(extracted_data, indent=2))
    
    final_result = {
        "timestamp": datetime.now().isoformat(),
        "document_data": extracted_data
    }
    
    save_to_json(final_result)
    return extracted_data

# Example usage:
#if __name__ == "__main__":
#    result = process_document("IMG_20250606_102038.jpg")
#    print("Final Result:")
#   print(json.dumps(result, indent=2))
