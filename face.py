import cv2
import numpy as np
import face_recognition
import os
from datetime import datetime, date, timedelta
from flask import Flask, flash, request, redirect, url_for, render_template, Response
from werkzeug.utils import secure_filename
import mysql.connector
from mysql.connector import Error

UPLOAD_FOLDER = 'data'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Function to check if the file has an allowed extension
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


app = Flask(__name__)
app.secret_key = "secret key"
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


# Function to encode images
def encoding_img(data):
    encodeList = []
    for img in data:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        encode = face_recognition.face_encodings(img)[0]
        encodeList.append(encode)
    return encodeList


# Function to establish a connection with the MySQL database
def create_connection():
    connection = None
    try:
        connection = mysql.connector.connect(
            host='JAYED',
            database='attendance',
            user='jayed',
            password='1234'
        )
        print("Connected to MySQL database")
    except Error as e:
        print(f"The error '{e}' occurred while connecting to the MySQL database")
    return connection


# Function to create the attendance and time tables if they don't exist
def create_tables(connection):
    try:
        cursor = connection.cursor()
        create_attendance_table_query = """
        CREATE TABLE IF NOT EXISTS attendance (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            time DATETIME NOT NULL
        )
        """
        cursor.execute(create_attendance_table_query)
        create_time_table_query = """
        CREATE TABLE IF NOT EXISTS time (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            intime DATETIME NOT NULL,
            outtime DATETIME,
            totaltime VARCHAR(10)
        )
        """
        cursor.execute(create_time_table_query)
        connection.commit()
        print("Attendance and Time tables created successfully")
    except Error as e:
        print(f"The error '{e}' occurred while creating the tables")


# Function to calculate the total time in the office
def calculate_total_time(intime, outtime):
    if outtime is None:
        return None

    time_format = '%H:%M'
    intime_str = intime.strftime('%Y-%m-%d %H:%M:%S')
    outtime_str = outtime.strftime('%Y-%m-%d %H:%M:%S')

    intime_obj = datetime.strptime(intime_str, '%Y-%m-%d %H:%M:%S')
    outtime_obj = datetime.strptime(outtime_str, '%Y-%m-%d %H:%M:%S')

    # Calculate the time difference
    time_diff = outtime_obj - intime_obj

    # Format the total time as HH:MM
    total_time = (datetime.min + time_diff).time().strftime(time_format)

    return total_time



# Function to take attendance and update the time table
def takeAttendance(name, connection):
    today = date.today()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    try:
        cursor = connection.cursor()

        # Check if the employee has an existing entry for the current date
        select_query = """
        SELECT id, intime, outtime
        FROM time
        WHERE name = %s
        AND DATE(intime) = %s
        """
        cursor.execute(select_query, (name, today))
        result = cursor.fetchone()

        if result:
            # If the employee already has an entry, update the outtime
            time_id, intime, _ = result
            update_query = """
            UPDATE time
            SET outtime = %s
            WHERE id = %s
            """
            cursor.execute(update_query, (now, time_id))
            connection.commit()
            print("Outtime updated successfully")
        else:
            # If the employee doesn't have an entry, insert a new row with intime
            insert_query = """
            INSERT INTO time (name, intime)
            VALUES (%s, %s)
            """
            cursor.execute(insert_query, (name, now))
            connection.commit()
            print("Intime recorded successfully")

        # Get the updated intime and outtime for calculating total time
        cursor.execute(select_query, (name, today))
        updated_result = cursor.fetchone()
        _, updated_intime, updated_outtime = updated_result

        # Calculate the total time
        total_time = calculate_total_time(updated_intime, updated_outtime)

        # Update the totaltime column
        update_total_time_query = """
        UPDATE time
        SET totaltime = %s
        WHERE id = %s
        """
        cursor.execute(update_total_time_query, (total_time, time_id))
        connection.commit()
        print("Total time updated successfully")

        # Insert the attendance record
        insert_attendance_query = """
        INSERT INTO attendance (name, time)
        SELECT %s, %s
        FROM DUAL
        WHERE NOT EXISTS (
            SELECT id
            FROM attendance
            WHERE name = %s
            AND time > DATE_SUB(NOW(), INTERVAL 900 SECOND)
        )
        """
        cursor.execute(insert_attendance_query, (name, now, name))
        connection.commit()
        print("Attendance recorded successfully")
    except Error as e:
        print(f"The error '{e}' occurred while inserting attendance record")



# Main function to connect to the database and perform attendance operations
def main():
    connection = create_connection()
    if connection is not None:
        create_tables(connection)
        # Close the connection
        if connection.is_connected():
            connection.close()
            print("MySQL database connection closed")


def gen():
    data = []
    filename = []
    dir_path = 'data'

    # Load images and filenames from the directory
    for imagess in os.listdir(dir_path):
        img_path = os.path.join(dir_path, imagess)
        img_path = face_recognition.load_image_file(img_path)
        data.append(img_path)
        filename.append(imagess.split(".", 1)[0])

    encodeListknown = encoding_img(data)
    cap = cv2.VideoCapture(0)

    while True:
        success, img = cap.read()
        imgc = cv2.resize(img, (0, 0), None, 0.25, 0.25)
        imgc = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        fasescurrent = face_recognition.face_locations(imgc)
        encode_fasescurrent = face_recognition.face_encodings(imgc, fasescurrent)

        # Compare faces in the current frame with known faces
        for encodeFace, faceloc in zip(encode_fasescurrent, fasescurrent):
            face_distence = face_recognition.face_distance(encodeListknown, encodeFace)
            if len(face_distence) > 0:
                matchindex = np.argmin(face_distence)
                matches_face = face_recognition.compare_faces(encodeListknown, encodeFace)

                if matches_face[matchindex]:
                    name = filename[matchindex].upper()
                    y1, x2, y2, x1 = faceloc
                    cv2.rectangle(img, (x1, y1), (x2, y2), (255, 0, 0), 2)
                    cv2.rectangle(img, (x1, y2 - 35), (x2, y2), (255, 0, 0), 2, cv2.FILLED)
                    cv2.putText(img, name, (x1 + 6, y2 - 6), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                    connection = create_connection()
                    if connection is not None:
                        takeAttendance(name, connection)
                        if connection.is_connected():
                            connection.close()
                            print("MySQL database connection closed")

        # Convert image to JPEG format for streaming
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
    main()
    app.run(debug=True)
