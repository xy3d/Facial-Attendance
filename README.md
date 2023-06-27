# Facial Attendance System with API and Database Integration

This repository contains two Python scripts: one for **Facial Attendance** using OpenCV and Haar cascades, and another for collecting data.

## Data Collector

<details>
  <summary><strong>Click for detailed instructions</strong></summary>

### Prerequisites

Make sure you have the required dependencies installed by running the following command:

```shell
pip install opencv-python
```

### Instructions

1. Clone or download this repository.

2. Open the terminal or command prompt and navigate to the repository's directory.

3. Run the following command to start the image capture script:

```shell
python image_capture.py
```

4. Enter the name of the person you want to capture images for.

5. The script will capture 20 images using the webcam and save them in the `data` folder, organized by person name.

6. Press 'q' to quit capturing images and move to the next person.
</details>

## Facial Attendance

<details>
  <summary><strong>Click for detailed instructions</strong></summary>

### Prerequisites

Make sure you have the required dependencies installed by running the following command:

```shell
pip install opencv-python flask mysql-connector-python
```

### Instructions

1. Open the terminal or command prompt and navigate to the repository's directory.

2. Run the following command to start the **Facial Attendance** application:

```shell
python face_recognition.py
```

3. Access the application by opening a web browser and visiting `http://localhost:5000`.

4. The webcam stream will be displayed, and the application will attempt to recognize faces based on the provided images in the `data` folder.

5. **Detected** faces will be highlighted in **Green**, and recognized persons will be displayed with their **name** and matching **percentage**. Unknown faces will be highlighted in **Red** and marked as "Unknown".

6. The application will also log the **Attendance, In/Out time log, and Record Anomalies** in a MySQL database.
</details>

## License

This project is licensed under the Apache-2.0 license.
