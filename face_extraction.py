import numpy as np
import cv2
from datetime import datetime
import face_recognition as fr

def faceextractor(img_path):
    
    face_classifier = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    image = cv2.imread(img_path)
    if image is None:
        print("Error: Image not found")
        return []

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    all_faces = []
    rotations = [
        (None, None), 
        (cv2.ROTATE_180, cv2.ROTATE_180),
        (cv2.ROTATE_90_CLOCKWISE, cv2.ROTATE_90_CLOCKWISE),
        (cv2.ROTATE_90_COUNTERCLOCKWISE, cv2.ROTATE_90_COUNTERCLOCKWISE)
    ]

    for rot_gray, rot_color in rotations:
        current_gray = gray if rot_gray is None else cv2.rotate(gray, rot_gray)
        current_image = image if rot_color is None else cv2.rotate(image, rot_color)

        faces = face_classifier.detectMultiScale(
            current_gray, 
            scaleFactor=1.3,
            minNeighbors=5,
            minSize=(30, 30)
        )

        if len(faces) > 0:
            for (x, y, w, h) in faces:
                all_faces.append({
                    'coords': (x, y, w, h),
                    'image': current_image,
                    'rotation': rot_gray
                })

    output_faces = []
    
    for face_info in all_faces:
        x, y, w, h = face_info['coords']
        current_image = face_info['image']
        
        x_pad = max(0, x - 25)
        y_pad = max(0, y - 40)
        w_pad = w + 50
        h_pad = h + 70
        
        face = current_image[y_pad:y_pad+h_pad, x_pad:x_pad+w_pad]
        
        if face.size == 0:
            continue
            
        try:
            rgb_face = cv2.cvtColor(face, cv2.COLOR_BGR2RGB)
            
            encodings = fr.face_encodings(rgb_face)
            if len(encodings) > 0:
                success, encoded_image = cv2.imencode('.jpg', face)
                if success:
                    output_faces.append(encoded_image.tobytes())
        except Exception as e:
            continue
    
    return output_faces