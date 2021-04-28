import cv2 as cv
import socket
import pickle
import struct
import time
from multiprocessing import Process as process
import functions as helper

HOST = '0.0.0.0'
#HOST = '127.0.0.1'
PORT = 8000
MAX_CLIENTS = 5
SECONDS = 10
PROCESSES = []
FRAMES = {}

def stream_camera(client, address):
    '''Stream video from a client'''

    package_size = struct.calcsize("P")
    while True:
        print(address, 'primary loop')
        data, message_size, msg_size = b'', None, None

        # Recieve data stream from socket (client)
        while len(data) < package_size:
            received = client.recv(4096)
            data += received

        message_size = data[:package_size]
        data = data[package_size:]
        msg_size = struct.unpack("P", message_size)[0]

        while len(data) < msg_size:
            print(len(data),'<',msg_size) # TODO: delete
            print('second loop: receiving data')  # TODO: delete
            data += client.recv(4096)

        pickled_data = data[:msg_size]
        data = data[msg_size:]=
        frame = pickle.loads(pickled_data)

        cv.imshow('streamed video', frame)
        cv.waitKey(1)

def main():
    print('socket server running')

    # Create Server (socket) and bind it to a address/port.
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(MAX_CLIENTS)
    print('Listening for sockets')

    while True:
        # Accept connection
        client, address = server.accept()
        print('Socket Connection:', address) # TODO: delete

        # Create, save, and start process (camera stream)
        p = process(target=stream_camera, args=(client, address, ))
        PROCESSES.append(p)
        p.start()

    # Clear PROCESSES
    for p in PROCESSES:
        p.join() # Join all PROCESSES

    socket.close() # TODO: see if this should be server.close() instead

if __name__ == '__main__':
    try:
        main()
    except:

        # TODO: move this back to main if necessary, and remove when done developing
        # Close server connection
        cv.destroyAllWindows()
