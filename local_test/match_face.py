import face_recognition as fr
import cv2
import time
import numpy as np
def load_and_encode(image_path):
        img = cv2.imread(image_path)
        img = cv2.flip(img, 1)
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        encodings = fr.face_encodings(rgb)
        if len(encodings) == 0:
            return -1
        return encodings[0]

def live_verification(i1_path, i2_path):
    # Load and encode reference images
    try:
        faceenc1 = load_and_encode(i1_path)
        faceenc2 = load_and_encode(i2_path)
    except Exception as e:
        print(f"Error loading reference images: {e}")
        return False

    # Verify the two reference images match each other first
    ref_match = fr.compare_faces([faceenc1], faceenc2)[0]
    if not ref_match:
        print("Reference images don't match each other!")
        return False

    # Video capture setup
    videocapture = cv2.VideoCapture(0)
    if not videocapture.isOpened():
        print("Could not open video capture")
        return False

    # Verification parameters
    matches_required = 10
    successful_matches = 0
    total_time = 30
    start_time = time.time()
    frame_count = 0

    while (time.time() - start_time < total_time and 
           successful_matches < matches_required):
        ret, frame = videocapture.read()
        if not ret:
            break

        try:
            # Process every 3rd frame to reduce computation
            if frame_count % 3 != 0:
                frame_count += 1
                continue

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            face_locations = fr.face_locations(rgb_frame)
            
            if len(face_locations) != 1:
                status = "Ensure one face in frame" if len(face_locations) == 0 else "Multiple faces detected"
                cv2.putText(frame, status, (50, 50), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
                cv2.imshow("Verification", frame)
                cv2.waitKey(1)
                frame_count += 1
                break

            # Get face encoding for current frame
            face_encoding = fr.face_encodings(rgb_frame, face_locations)[0]
            
            # Compare with both reference faces
            match1 = fr.compare_faces([faceenc1], face_encoding)[0]
            match2 = fr.compare_faces([faceenc2], face_encoding)[0]
            dist1 = fr.face_distance([faceenc1], face_encoding)[0]
            dist2 = fr.face_distance([faceenc2], face_encoding)[0]

            # Draw rectangle and text
            top, right, bottom, left = face_locations[0]
            color = (0, 255, 0) if dist1<=0.50 and dist2<=0.50 else (0, 0, 255)
            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
            
            status = f"Match {successful_matches+1}/{matches_required}" if dist1<=0.50 and dist2<=0.50 else "No match"
            cv2.putText(frame, f"{status} D1:{dist1:.2f} D2:{dist2:.2f}", 
                       (left, top-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
            
            cv2.imshow("Verification", frame)
            cv2.waitKey(1)
            
            if dist1<=0.50 and dist2<=0.50:
                successful_matches += 1
            
            frame_count += 1

        except Exception as e:
            print(f"Error processing frame: {e}")
            frame_count += 1

    videocapture.release()
    cv2.destroyAllWindows()

    final_result = successful_matches >= 8
    print(f"Verification {'successful' if final_result else 'failed'}. Matches: {successful_matches}/{matches_required}")
    return final_result

# Example usage
result = live_verification("IMG_20250613_102246.jpg", "face_20250623_160717_0.jpg")
print(f"Final verification result: {result}")