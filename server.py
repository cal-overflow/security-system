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
MAX_CLIENTS = 5
CLIENTS = 0
SECONDS = 10
PROCESSES = []
FRAMES = {}

def stream_camera(client, address, CLIENTS):
    '''Stream video from a client'''

    #TODO: fix this
    if CLIENTS >= 5:
        return

    FRAMES[address[1]] = []
    package_size = struct.calcsize("P")
    recording = False
    while True:
        data, message_size, msg_size = b'', None, None
        print('hello')
        # Recieve data stream from socket (client)

        while len(data) < package_size:
            received = client.recv(4096)
            print('first while loop')

            if not received:
                # Close connection since nothing was received (client is not communicating)
                client.close()
                print('Socket {} disconnected'.format(address[1]))
                # TODO: remove this (id) process (maybe)
                # YES! I was correct. Must remove this process/id. I don't think this is working yet...
                #PROCESSES.pop(CLIENTS) #TODO need to figure this out (no longer pass id as param)
                FRAMES.pop(address[1], None)
                print(CLIENTS)
                CLIENTS -= 1

                # Cheap solution. #TODO: Fix this
                with open('clients.txt', 'w') as file:
                    file.write(str(CLIENTS))
                return # exit function
            else:
                data += received

        message_size = data[:package_size]
        data = data[package_size:]
        msg_size = struct.unpack("P", message_size)[0]

        while len(data) < msg_size:
            print(len(data),'<',msg_size)
            print('second while loop')
            data += client.recv(4096)

        pickled_data = data[:msg_size]
        data = data[msg_size:]
        data = pickle.loads(pickled_data)

        # Update frames
        temp_frames = FRAMES[address[1]]
        temp_frames.append(data)
        if len(temp_frames) > data['FPS'] * SECONDS and not recording:
            temp_frames.pop(0)
        FRAMES[address[1]] = temp_frames

        processed_frame = FRAMES[address[1]][-1]['FRAME']
        print('what')

        # If there is motion in this frame or there was recently motion (and it is recording), then act accordingly
        #if data['MOTION'] or recording:
            #recording, output_file = cf.record(FRAMES[address[1]], recording, SECONDS)
            #processed_frame = cf.drawRecording(FRAMES[address[1]][-1]['FRAME'], FRAMES[address[1]][-1]['WIDTH'], FRAMES[address[1]][-1]['HEIGHT'])

            #if not recording:
                # No longer recording. Throw away all but last few FRAMES
                #temp_frames = FRAMES[address[1]]
                #temp_frames = temp_frames[(len(temp_frames) - (data['FPS'] * SECONDS)):]
                #FRAMES[address[1]] = temp_frames
                #print('Video saved to', output_file)


        # Write this last frame to a file called <CLIENTS (or the id of this client)>.jpg, which will then be used by flask server
        # 9 millisecond intervals where ms 0-5 are for reading # TODO: fix this (see webserver.py's TODO comments)
        if (0 <= int(time.time() * 1000) % 10 <= 5):
            filename = 'stream_frames/{}.jpg'.format(CLIENTS)
            cv.imwrite(filename, processed_frame)

        cv.imshow('Client: {} ({})'.format(address[1], address[0]), processed_frame)
        cv.waitKey(1)

if __name__ == '__main__':
    print('socket server running')
    # Create Server (socket) and bind it to a address/port.
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(MAX_CLIENTS)
    print('Listening for sockets')

    while True:
        with open('clients.txt', 'w') as file:
            file.write(str(CLIENTS))

        # Accept connection
        client, address = server.accept()
        CLIENTS += 1
        print('Socket Connection:', address) # TODO: delete

        # Create, save, and start process (camera stream)
        p = process(target=stream_camera, args=(client, address, CLIENTS))
        PROCESSES.append(p)
        p.start()

    # Clear PROCESSES
    for p in PROCESSES:
        p.join() # Join all PROCESSES


    with open('clients.txt', 'w') as file:
        file.write(str(0)) # Ensure that server knows no clients are connected when it restarts. (Connection will be re-established)

    # Close server connection
    cv.destroyAllWindows()
    socket.close()
