import cv2
import numpy as np
import face_recognition
import os
from datetime import datetime, date
from flask import Flask, flash, request, redirect, url_for, render_template, Response
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'data'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


app = Flask(__name__)

# app.secret_key = "secret key"

# Configure the upload folder for file uploads
# Uploaded files will be stored in the 'UPLOAD_FOLDER' directory
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def upload_file():
    return render_template('upload.html')


@app.route('/success', methods=['GET', 'POST'])
def success():
    if 'file' not in request.files:
        return render_template('upload.html')
    file = request.files['file']
    if file.filename == '':
        return render_template('upload.html')
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return render_template('upload.html')
    else:
        return render_template('upload.html')


@app.route('/index')
def index():
    """Video streaming home page."""
    return render_template('index.html')


def gen():
    data = []                   # List to store loaded images
    filename = []               # List to store image filenames
    dir_path = 'data'           # Directory path where images are stored

    # Loop through the images in the directory
    for imagess in os.listdir(dir_path):
        img_path = os.path.join(dir_path, imagess)              # Get the full image path
        img_path = face_recognition.load_image_file(img_path)   # Load the image file        
        data.append(img_path)                                   # Add the loaded image to the data list        
        filename.append(imagess.split(".", 1)[0])               # Extract the filename without the extension
        

    def encoding_img(data):       
        encodeList = []                                         # List to store the face encodings
        
        # Iterate over each image in the data
        for img in data:                                    
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)          # Convert the image to RGB format
            encode = face_recognition.face_encodings(img)[0]    # Encode the face in the image
            encodeList.append(encode)                           # Append the face encoding to the list

        # Return the list of face encodings
        return encodeList


def takeAttendance(name):
    # Get today's date
    today = date.today()

    # Generate the filename using the current date
    filename = today.strftime("%d-%m-%Y") + '.csv'

    # Open the CSV file in 'a+' mode (append or create if it doesn't exist)
    with open(filename, 'a+') as f:
        f.seek(0)                                       # Move the file pointer to the beginning of the file
        mypeople_list = f.readlines()                   # Read all the lines in the file
        nameList = []                                   # Create a list to store the names already present in the file

        # Iterate through each line in the file
        for line in mypeople_list:
            entry = line.split(',')                     # Split the line into separate entries
            nameList.append(entry[0])                   # Add the name to the nameList

        # Check if the name is not already in the nameList
        if name not in nameList:
            now = datetime.now()                        # Get the current timestamp
            datestring = now.strftime('%H:%M:%S')       # Formatting
            f.writelines(f'\n{name},{datestring}')      # Write the name and timestamp to the file as a new line

            # Check if the file is empty (size is 0)
            if f.tell() == 0:
                f.writelines("name,time")               # If the file is empty, write column headers as the first line
                f.writelines(f'\n{name},{datestring}')  # Write the name and timestamp as the second line


    encodeListknown = encoding_img(data)                # Encoding the known images from the 'data' list

    cap = cv2.VideoCapture(0)                           # Initializing video capture from webcam

    while True:
        success, img = cap.read()                       # Reading a frame from the webcam

        # Preprocessing the image
        imgc = cv2.resize(img, (0, 0), None, 0.25, 0.25)    # Resizing the image for faster processing
        imgc = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)         # Converting the image from BGR to RGB

        # Detecting faces in the current frame
        fasescurrent = face_recognition.face_locations(imgc)
        encode_fasescurrent = face_recognition.face_encodings(imgc, fasescurrent)

        for encodeFace, faceloc in zip(encode_fasescurrent, fasescurrent):
            # Comparing the face encodings with the known encodings
            face_distence = face_recognition.face_distance(encodeListknown, encodeFace)
            
            if len(face_distence) > 0:
                matchindex = np.argmin(face_distence)
                matches_face = face_recognition.compare_faces(encodeListknown, encodeFace)
                
                if matches_face[matchindex]:
                    name = filename[matchindex].upper()
                    y1, x2, y2, x1 = faceloc
                    
                    # Drawing bounding box and name label on the face in the frame
                    cv2.rectangle(img, (x1, y1), (x2, y2), (255, 0, 0), 2)
                    cv2.rectangle(img, (x1, y2 - 35), (x2, y2), (255, 0, 0), 2, cv2.FILLED)
                    cv2.putText(img, name, (x1 + 6, y2 - 6), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

                    takeAttendance(name)                # Recording the attendance

        frame = cv2.imencode('.jpg', img)[1].tobytes()
        yield (b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        key = cv2.waitKey(20)
        if key == 27:
            break


@app.route('/video_feed')
def video_feed():
    """Video streaming route. Put this in the src attribute of an img tag."""
    return Response(gen(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == "__main__":
    app.run(debug=True)
