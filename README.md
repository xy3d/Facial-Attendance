# Facial Attendance with API and SQL integration

This repository contains two Python scripts: one for face recognition using OpenCV and Haar cascades, and another for capturing images using a webcam.

## Requirements

- Python 3.x
- OpenCV (cv2)
- Flask
- mysql-connector-python

## Usage

### Image Capture

1. Make sure you have the required dependencies installed by running the following command:
   ```shell
   pip install opencv-python
   
2. Clone or download this repository.

3. Open the terminal or command prompt and navigate to the repository's directory.

4. Run the following command to start the image capture script:

   ```shell
   python image_capture.py
   
5. Enter the name of the person you want to capture images for. Repeat this step to capture images for multiple persons.

6. The script will capture 20 images using the webcam and save them in the data folder, organized by person name.

7. Press 'q' to quit capturing images and move to the next person.

Note: Repeat steps to capture images for additional persons.


### Face Attendance
1. Make sure you have the required dependencies installed by running the following command:

   ```shell
   pip install opencv-python flask mysql-connector-python

2. Open the terminal or command prompt and navigate to the repository's directory.

Run the following command to start the face recognition application:

shell
Copy code
python face_recognition.py
Access the application by opening a web browser and visiting http://localhost:5000.

The webcam stream will be displayed, and the application will attempt to recognize faces based on the provided images in the data folder.

Detected faces will be highlighted in green, and recognized persons will be displayed with their names and matching percentages. Unknown faces will be marked as "Unknown".

The application will also log the attendance and record anomalies in a MySQL database.

License
This project is licensed under the MIT License.
