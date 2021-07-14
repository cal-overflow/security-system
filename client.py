import cv2 as cv
import socket
import pickle
import time
import datetime
from systemhelper import struct, timestamp, drawTime

# Server address and port
HOST = '127.0.0.1' # Replace with the server address/url
PORT = 8080
THRESHOLD = 7500 # Movement detection threshold

def main():
    '''Client that connects and streams video to server.'''

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.connect((HOST, PORT))

    confirmRelationship(server)
    print('{} [CLIENT]: Established connection with server'.format(timestamp()))

    # Set and calibrate camera
    camera, FPS = calibrateCamera()

    print('{} [CLIENT]: Beginning stream to server'.format(timestamp()))
    ret, frame1 = camera.read()
    ret, frame2 = camera.read()
    connection_failed = False

    while camera.isOpened():
        detected_motion, motion_frame = detectMotion(frame1, frame2)
        frame = drawTime(motion_frame, int(camera.get(3)), int(camera.get(4)))
        data = {'FRAME': frame,
                'MOTION': detected_motion,
                'FPS': FPS,
                'WIDTH': int(camera.get(3)),
                'HEIGHT': int(camera.get(4))
                }
        pickled_data = pickle.dumps(data)

        try:
            server.sendall(struct.pack("P", len(pickled_data))+pickled_data)

        except socket.error:
            # Handle connection issues
            print('{} [CLIENT]: Connection to server disrupted'.format(timestamp()))
            connected = False
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            while not connected:
                # Try to reconnect
                try:
                    server.connect((HOST, PORT))
                    confirmRelationship(server)
                    connected = True
                    if connection_failed:
                        # Connection was re-established after it recently failed
                        print('{} [CLIENT]: Re-established connection with server'.format(timestamp()))
                        connection_failed = False
                except socket.error:
                    connected = False
                    connection_failed = True
                    camera.release()
                    time.sleep(2.5) # Wait before trying to reconnect
                    print('{} [CLIENT]: Attempting to re-establish connection with server'.format(timestamp()))
                    camera.open(0)

        frame1 = frame2
        ret, frame2 = camera.read()
        cv.waitKey(1)

def confirmRelationship(server):
    '''Confirm relationship with server. This acts as an extra
    handshake that must be made between client and server.'''
    server.send(b'confirmation')

def calibrateCamera():
    '''Calibrate the camera. Get the true FPS (including processing) from the camera'''
    print('{} [CLIENT]: Calibrating camera'.format(timestamp()))
    camera = cv.VideoCapture(0)
    width = camera.get(cv.CAP_PROP_FRAME_WIDTH)
    height = camera.get(cv.CAP_PROP_FRAME_HEIGHT)

    # Adjust frame size if it is excessively large
    while width * height  >= 1000000:
        width *= 0.75
        height *= 0.75

    # OpenCV will override input and round to the closest (recognized) resolution. For example, I set res to 1900x1070 and it will override as 1920x1080.
    camera.set(3, width)
    camera.set(4, height)

    if not camera.isOpened():
        # Attempt to open capture device once more, after a failure
        camera.open()
        if not camera.isOpened():
            print('{} [CLIENT]: Issue opening camera'.format(timestamp()))
            exit()

    start_time = time.time()
    count = 0
    while int(time.time() - start_time) < 10:
        ret, frame = camera.read()
        count += 1 # number of frames

    return camera, int(count / 10)

def detectMotion(frame1, frame2):
    '''Detect motion given two frames. Returns boolean and frame with motion area outlined.'''
    # Helpful Source: Divyanshu Shekhar - https://divyanshushekhar.com/motion-detection-opencv/
    difference = cv.absdiff(frame1, frame2)
    gray_difference = cv.cvtColor(difference, cv.COLOR_BGR2GRAY)
    blur = cv.GaussianBlur(gray_difference, (5, 5), 0)
    __, thresh = cv.threshold(blur, 20, 255, cv.THRESH_BINARY)
    dilated = cv.dilate(thresh, None, iterations=3)
    contours, __ = cv.findContours(dilated, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)

    detected = False
    frame = frame1.copy()
    for contour in contours:

        (x, y, w, h) = cv.boundingRect(contour)
        # Place date on frame regardless of any movement
        if cv.contourArea(contour) >= THRESHOLD:
            detected = True

            cv.rectangle(frame, (x, y), (x+w, y+h), (255, 255, 255), 1)
            cv.putText(frame, 'MOTION', (10, 20), cv.FONT_HERSHEY_PLAIN, 1.25, (0, 0, 224), 2, cv.FILLED, False)

    return detected, frame

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print('{} [CLIENT]: Exiting script because of error:\n{}'.format(timestamp(), e))
