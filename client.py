import cv2 as cv
import socket
import pickle
import struct
import time
import datetime
import cameraFunctions as cf

#HOST = '192.168.0.8' # Server address
HOST = '127.0.0.1'
PORT = 8000

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.connect((HOST, PORT))

FPS = cf.getFPS()

camera = cv.VideoCapture(0)
if not camera.isOpened():
    # Attempt to open capture device once more, after a failure
    camera.open()
    if not camera.isOpened():
        print('Cannot open camera')
        exit()

ret, frame1 = camera.read()
ret, frame2 = camera.read()

while camera.isOpened():
    detected_motion, motion_frame = cf.detectMotion(frame1, frame2, int(camera.get(3)), int(camera.get(4)))
    frame = cf.drawTime(motion_frame, int(camera.get(3)), int(camera.get(4)))
    data = {'FRAME': frame,
            'MOTION': detected_motion,
            'FPS': FPS,
            'WIDTH': int(camera.get(3)),
            'HEIGHT': int(camera.get(4))
            }
    pickled_data = pickle.dumps(data)

    try:
        server.sendall(struct.pack("L", len(pickled_data))+pickled_data)

    # Handle connection issue
    except:
        connected = False
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Try to reconnect
        while not connected:
            try:
                server.connect((HOST, PORT))
                connected = True
                # Connection re-established
            except socket.error:
                camera.release()
                time.sleep(5) # wait 5 seconds before trying to reconnect
                camera.open()

    frame1 = frame2
    ret, frame2 = camera.read()
    cv.waitKey(1)

#helpful resources:
#https://stackoverflow.com/questions/30988033/sending-live-video-frame-over-network-in-python-opencv#
#https://stackoverflow.com/questions/53347759/importerror-libcblas-so-3-cannot-open-shared-object-file-no-such-file-or-dire
#https://stackoverflow.com/questions/54665842/when-importing-tensorflow-i-get-the-following-error-no-module-named-numpy-cor
#https://stackoverflow.com/questions/34051737/numpy-core-multiarray-failed-to-import
#https://stackoverflow.com/questions/10810249/python-socket-multiple-clients
#https://instructobit.com/tutorial/101/Reconnect-a-Python-socket-after-it-has-lost-its-connection



#motion detected checklist:
#x - send notification to server
# record() function

#video = record() # this will record last 15 seconds and keep recording NO movement is detected for 15 simultaneous seconds
#Send the video to the server
