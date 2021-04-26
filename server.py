import cv2 as cv
import socket
import pickle
import struct
import time
from multiprocessing import Process as process
import cameraFunctions as cf

#HOST = '0.0.0.0'
HOST = '127.0.0.1'
PORT = 8000
processes = []
frames = {}
SECONDS = 10

def stream_camera(client, address):
    '''Handle a client connecting'''

    frames[address[1]] = []
    package_size = struct.calcsize("P")
    recording = False
    while True:
        data, message_size, msg_size = b'', None, None
        # Recieve data stream from socket (client)

        while len(data) < package_size:
            received = client.recv(4096)

            if not received:
                # Close connection since nothing was received (client is not communicating)
                client.close()
                print('Socket {} disconnected'.format(address[1]))
                frames.pop(address[1], None)
                return
            else:
                data += received

        message_size = data[:package_size]
        data = data[package_size:]
        msg_size = struct.unpack("P", message_size)[0]

        while len(data) < msg_size:
            data += client.recv(4096)

        pickled_data = data[:msg_size]
        data = data[msg_size:]
        data = pickle.loads(pickled_data)
        # data = {'img': image, 'motion': boolean, 'FPS': fps, 'WIDTH': width, 'HEIGHT': height}

        temp_frames = frames[address[1]]
        temp_frames.append(data)
        if len(temp_frames) > data['FPS'] * SECONDS and not recording:
            temp_frames.pop(0)
        frames[address[1]] = temp_frames

        processed_frame = frames[address[1]][-1]['FRAME']

        if data['MOTION'] or recording:
            recording, output_file = cf.record(frames[address[1]], recording, SECONDS)
            processed_frame = cf.drawRecording(frames[address[1]][-1]['FRAME'], frames[address[1]][-1]['WIDTH'], frames[address[1]][-1]['HEIGHT'])

            if not recording:
                # No longer recording. Throw away all but last few frames
                temp_frames = frames[address[1]]
                temp_frames = temp_frames[(len(temp_frames) - (data['FPS'] * SECONDS)):]
                frames[address[1]] = temp_frames
                print('Video saved to', output_file)

        cv.imshow('Client: {} ({})'.format(address[1], address[0]), processed_frame)
        cv.waitKey(1)

# Create Server (socket) and bind it to a address/port.
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen(5) # maximum of 5 sockets (devices) can connect. This can be increased
print('Listening for sockets')

while True:
    # Accept connection
    client, address = server.accept()
    print('Socket Connection:', address)

    # Create, save, and start process (camera stream)
    p = process(target=stream_camera, args=(client, address,))
    processes.append(p)
    p.start()

# Clear processes
for p in processes:
    p.join() # Joining all processes

# Close server connection
cv.destroyAllWindows()
socket.close()
