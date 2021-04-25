import cv2 as cv
#import numpy
import socket
#import sys
import pickle
import struct

HOST = ''
PORT = 8080

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print('socket created')

server.bind((HOST, PORT))
print('socket binding complete')

server.listen(5) # maximum of 5 sockets (devices) can connect. This can be increased
print('Server listening for sockets')

# Accept connection (TODO: might need to move this inside while loop)
client, address = server.accept()

# Data is initially empty
data = b''
package_size = struct.calcsize("L")
count = 0
while True:
    while len(data) < package_size:
        data += client.recv(4096)

    message_size = data[:package_size]
    data = data[package_size:]
    msg_size = struct.unpack("L", message_size)[0]

    while len(data) < msg_size:
        data += client.recv(4096)

    frame = data[:msg_size]
    data = data[msg_size:]
    frame = pickle.loads(frame)

    count += 1
    cv.imshow('Streamed Video', frame)

    # TODO: remove this
    if cv.waitKey(1) == ord('q'):
        break

cv.destroyAllWindows()
