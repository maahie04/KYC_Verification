import numpy as np
import cv2
from datetime import datetime
import face_recognition as fr


def faceextractor(img_path):
# Load the Haar Cascade classifier

    face_classifier = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    # Load image and convert to grayscale
    image = cv2.imread(img_path)
    imagecopy=cv2.imread(img_path)
    if image is None:
        print("Error: Image not found")
        exit()

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Detect faces
    faces = face_classifier.detectMultiScale(
        gray, 
        scaleFactor=1.3,
        minNeighbors=5,
        minSize=(30, 30)
    )
    count=0

    while(count<4 and len(faces)==0):
        if count==0:
            rotated = cv2.rotate(gray, cv2.ROTATE_180)
            imagecopy = cv2.rotate(image, cv2.ROTATE_180)
            faces = face_classifier.detectMultiScale(
                rotated, 
                scaleFactor=1.3,
                minNeighbors=5,
                minSize=(30, 30)
            )
        elif count==1:
            rotated = cv2.rotate(gray, cv2.ROTATE_90_CLOCKWISE)
            imagecopy = cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
            faces = face_classifier.detectMultiScale(
                rotated, 
                scaleFactor=1.3,
                minNeighbors=5,
                minSize=(30, 30)
            )
        else:
            rotated = cv2.rotate(gray, cv2.ROTATE_90_COUNTERCLOCKWISE)
            imagecopy = cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)
            faces = face_classifier.detectMultiScale(
                rotated, 
                scaleFactor=1.3,
                minNeighbors=5,
                minSize=(30, 30)
            )
        count=count+1      
    if len(faces) == 0:
        print("No faces found")
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save the original image with rectangles
        output_image = imagecopy.copy()
        output_faces=[]
        for i, (x, y, w, h) in enumerate(faces):
            # Add padding to the bounding box
            x_pad = max(0, x - 25)
            y_pad = max(0, y - 40)
            w_pad = w + 50
            h_pad = h + 70
        
        # Draw rectangle on the output image
            cv2.rectangle(output_image, (x_pad, y_pad), (x_pad + w_pad, y_pad + h_pad), (27, 200, 10), 2)
        
        # Extract and save the face
            face = imagecopy[y_pad:y_pad+h_pad, x_pad:x_pad+w_pad]
            rgb1 = cv2.cvtColor(face, cv2.COLOR_BGR2RGB)
            try:
                faceenc1 = fr.face_encodings(rgb1)[0]
                if face.size > 0 and len(faceenc1)>0:  # Check if face region is valid
                    face_filename = f"face_{timestamp}_{i}.jpg"
                    cv2.imwrite(face_filename, face)
                    print(f"Saved face to {face_filename}")
                    annotated_filename = f"annotated_{timestamp}_{i}.jpg"
                    cv2.imwrite(annotated_filename, output_image)
                    print(f"Saved annotated image to {annotated_filename}")
                    output_faces.append(face_filename)
            except Exception as e:
                continue
    
    # Save the annotated image
            
            
        return output_faces
    
