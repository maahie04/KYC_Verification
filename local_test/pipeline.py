import document_verification_extraction
import local_test.match_face as match_face
import haar
import face_recognition as fr
import local_test.signature as signature
img_path1 = '<Photo of ID card>'
img_path2 = '<Passport sized high quality photo>'
document_verification_extraction.initialization(img_path1)
faces= haar.faceextractor(img_path1)
for file in faces:
    a= match_face.load_and_encode(file)
    if(a.all()==-1):
        continue
    match_face.live_verification(img_path1,img_path2)
signature.signcap()
