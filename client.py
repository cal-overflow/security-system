import cv2 as cv
#import numpy
import socket
#import sys
import pickle
import struct

HOST = '127.0.0.1' # Raspberry Pi (local) address
PORT = 8080

socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
socket.connect((HOST, PORT))

camera = cv.VideoCapture(0)
if not camera.isOpened():
    #Attempt to open capture device once more, after a failure
    camera.open()
    if not camera.isOpened():
        print('Cannot open camera')
        exit()

# Camera properties
#width = int(camera.get(3))
#height = int(camera.get(4))
#fps = camera.get(5)

while camera.isOpened():
    ret, frame = camera.read()
    data = pickle.dumps(frame)
    socket.sendall(struct.pack("L", len(data))+data)
