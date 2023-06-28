import cv2
import numpy as np
import os
from datetime import datetime, date, timedelta
from flask import Flask, render_template, Response, jsonify
import mysql.connector
from mysql.connector import Error


UPLOAD_FOLDER = 'data'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)
app.secret_key = "secret key"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


# Function to check if the file has an allowed extension
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    """Video streaming home page."""
    return render_template('index.html')


# @app.route('/dashboard')
# def dashboard():
#     """Dashboard page."""
#     connection = create_connection()
#     attendance_data = get_table_data(connection, 'attendance')
#     time_data = get_table_data(connection, 'time')
#     anomaly_data = get_table_data(connection, 'anomaly')
#     return jsonify({
#         'attendance': attendance_data,
#         'time': time_data,
#         'anomaly': anomaly_data
#     })


@app.route('/dashboard')
def dashboard():
    """Dashboard page."""
    connection = mysql.connector.connect(
            host='JAYED',
            database='attendance',
            user='jayed',
            password='1234'
    )  # Replace with your actual MySQL connection details

    cursor = connection.cursor()

    # Fetch data from the 'attendance' table
    cursor.execute('SELECT * FROM attendance')
    attendance_data = cursor.fetchall()

    # Fetch data from the 'time' table
    cursor.execute('SELECT * FROM time')
    time_data = cursor.fetchall()

    # Fetch data from the 'anomaly' table
    cursor.execute('SELECT * FROM anomaly')
    anomaly_data = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template('dashboard.html', attendance_data=attendance_data, time_data=time_data, anomaly_data=anomaly_data)


# Function to fetch data from a table in the database
def get_table_data(connection, table_name):
    try:
        cursor = connection.cursor()
        select_query = f"SELECT * FROM {table_name}"
        cursor.execute(select_query)
        rows = cursor.fetchall()
        column_names = [desc[0] for desc in cursor.description]
        data = []
        for row in rows:
            data.append(dict(zip(column_names, row)))
        return data
    except Error as e:
        print(f"The error '{e}' occurred while fetching data from the table {table_name}")
        return []


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
        create_anomaly_table_query = """
        CREATE TABLE IF NOT EXISTS anomaly (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            intime DATETIME NOT NULL,
            outtime DATETIME,
            totaltime VARCHAR(10),
            date DATE NOT NULL
        )
        """
        cursor.execute(create_anomaly_table_query)
        connection.commit()
        print("Attendance, Time, and Anomaly tables created successfully")
    except Error as e:
        print(f"The error '{e}' occurred while creating the tables")


# Function to retrieve attendance data from the database
def get_attendance_data(connection):
    try:
        cursor = connection.cursor()
        select_query = """
        SELECT *
        FROM attendance
        ORDER BY time DESC
        """
        cursor.execute(select_query)
        attendance_data = cursor.fetchall()
        return attendance_data
    except Error as e:
        print(f"The error '{e}' occurred while retrieving attendance data")


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


def is_anomaly(total_time):
    if total_time is not None:
        hours, minutes = total_time.split(':')
        total_hours = int(hours) + int(minutes) / 60
        if total_hours < 8:
            return True
    return False


def takeAttendance(name, connection):
    today = date.today()
    now = datetime.now()

    try:
        cursor = connection.cursor()

        # Check if the employee has an existing entry for the current date
        select_query = """
        SELECT id, intime, outtime, totaltime
        FROM time
        WHERE name = %s
        AND DATE(intime) = %s
        """
        cursor.execute(select_query, (name, today))
        result = cursor.fetchone()

        if result:
            # If the employee already has an entry, update the outtime
            time_id, intime, _, total_time = result
            update_query = """
            UPDATE time
            SET outtime = %s
            WHERE id = %s
            """
            cursor.execute(update_query, (now, time_id))
            connection.commit()
            # print("Outtime updated successfully")
        else:
            # If the employee doesn't have an entry for the current date, insert a new row with intime
            insert_query = """
            INSERT INTO time (name, intime)
            VALUES (%s, %s)
            """
            cursor.execute(insert_query, (name, now))
            connection.commit()
            # print("Intime recorded successfully")

            # Retrieve the newly inserted time_id
            time_id = cursor.lastrowid

        # Get the updated intime and outtime for calculating total time
        cursor.execute(select_query, (name, today))
        updated_result = cursor.fetchone()
        _, updated_intime, updated_outtime, total_time = updated_result

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
        # print("Total time updated successfully")

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
        # print("Attendance recorded successfully")

        # Check if the total time is an anomaly and occurred more than 24 hours ago
        if total_time and is_anomaly(total_time) and (now - updated_intime) > timedelta(hours=24):
            # Insert the anomaly record
            insert_anomaly_query = """
            INSERT INTO anomaly (name, intime, outtime, totaltime, date)
            VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(insert_anomaly_query, (name, updated_intime, updated_outtime, total_time, today))
            connection.commit()
            print("Anomaly recorded successfully")

    except Error as e:
        print(f"The error '{e}' occurred while inserting attendance record")


def gen():
    data = []
    dir_path = 'data'

    # Load images and folder names from the directory
    for person_folder in os.listdir(dir_path):
        person_folder_path = os.path.join(dir_path, person_folder)
        if os.path.isdir(person_folder_path):
            for imagess in os.listdir(person_folder_path):
                img_path = os.path.join(person_folder_path, imagess)
                img = cv2.imread(img_path)
                data.append(img)

    cap = cv2.VideoCapture(0)

    consecutive_frames_required = 5  # Number of consecutive frames required for a valid match
    consecutive_frames_detected = 0  # Counter for consecutive frames with a detected face
    match_found = False  # Flag to indicate if a match has been found

    while True:
        success, img = cap.read()
        img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Detect faces in the grayscale image
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        faces = face_cascade.detectMultiScale(img_gray, 1.3, 5)

        if len(faces) > 0:
            consecutive_frames_detected += 1
        else:
            consecutive_frames_detected = 0

        if consecutive_frames_detected == consecutive_frames_required:
            # Face detected in multiple consecutive frames
            for (x, y, w, h) in faces:
                roi_gray = img_gray[y:y + h, x:x + w]

                # Flag to check if a match is found
                match_found = False

                for stored_img in data:
                    stored_img_gray = cv2.cvtColor(stored_img, cv2.COLOR_BGR2GRAY)
                    stored_img_gray = cv2.resize(stored_img_gray, (w, h))
                    diff = cv2.absdiff(roi_gray, stored_img_gray)
                    diff_mean = np.mean(diff)
                    matching_percentage = (1 - diff_mean / 255) * 100

                    if matching_percentage > 80:
                        takeAttendance(person_folder, connection)
                        cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 3)
                        cv2.putText(img, f"{person_folder} ({matching_percentage:.2f}%)", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
                        match_found = True
                        print(f"Detected: {person_folder} ({matching_percentage:.2f}%)")
                        break

                if not match_found:
                    # If no match is found, display "Unknown"
                    cv2.rectangle(img, (x, y), (x + w, y + h), (0, 0, 255), 3)
                    cv2.putText(img, "Unknown", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
                    print("Detected: Unknown")

        elif consecutive_frames_detected < consecutive_frames_required:
            # Reset the match_found flag and consecutive_frames_detected counter
            match_found = False

        ret, buffer = cv2.imencode('.jpg', img)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

    cap.release()


@app.route('/video_feed')
def video_feed():
    """Video streaming route. Put this in the src attribute of an img tag."""
    return Response(gen(), mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == '__main__':
    connection = create_connection()
    create_tables(connection)
    app.run(debug=True, host='0.0.0.0', port=5000)
