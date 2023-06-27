import cv2
import os
import time

# Function to capture images
def capture_images(name, output_folder):
    # Create a directory for the person if it doesn't exist
    person_folder = os.path.join(output_folder, name)
    os.makedirs(person_folder, exist_ok=True)

    # Initialize the webcam
    cap = cv2.VideoCapture(0)

    # Capture 20 images
    count = 0
    while count < 20:
        ret, frame = cap.read()

        # Display the frame
        cv2.imshow('Capture Images', frame)

        # Introduce a delay of 0.5 seconds
        time.sleep(0.5)

        # Save the frame as an image
        image_path = os.path.join(person_folder, f'{name}_{count}.jpg')
        cv2.imwrite(image_path, frame)

        count += 1

        # Break the loop when 20 images are captured
        if count == 20:
            break

        # Break the loop and move to the next person when 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Release the webcam and destroy the window
    cap.release()
    cv2.destroyAllWindows()


# Define the output folder
output_folder = 'data'

# Get user input for person names
while True:
    name = input("Enter the name of the person (or 'q' to quit): ")
    if name.lower() == 'q':
        break

    # Capture images for the person
    capture_images(name, output_folder)

print("Image capture completed.")
