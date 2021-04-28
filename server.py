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

    #TODO: fix this
    if helper.getClientCount() >= 5:
        return

    alternator = True
    FRAMES[address[1]] = []
    package_size = struct.calcsize("P")
    recording = False
    while True:
        #print(address, 'here')
        data, message_size, msg_size = b'', None, None

        # Recieve data stream from socket (client)
        while len(data) < package_size:
            received = client.recv(4096)

            if not received:
                # Close connection since nothing was received (client is not communicating)
                client.close()
                print('Socket {} disconnected'.format(address[1]))
                # TODO: remove this (id) process (maybe)
                # YES! I was correct. Must remove this process/id. I don't think this is working yet...
                #PROCESSES.pop(CLIENTS) #TODO need to figure this out (no longer pass id as param)
                FRAMES.pop(address[1], None)
                helper.updateClientCount(helper.getClientCount() - 1)
                print(helper.getClientCount())
                return # exit function
            else:
                data += received

        message_size = data[:package_size]
        data = data[package_size:]
        msg_size = struct.unpack("P", message_size)[0]
        print(msg_size) # TODO: DELETE

        while len(data) < msg_size:
            data += client.recv(4096)

        if address[0] != '127.0.0.1': # TODO: delete
            print('package received', address[1]) # TODO: delete
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

        # If there is motion in this frame or there was recently motion (and it is recording), then act accordingly
        #if data['MOTION'] or recording:
            #recording, output_file = helper.record(FRAMES[address[1]], recording, SECONDS)
            #processed_frame = helper.drawRecording(FRAMES[address[1]][-1]['FRAME'], FRAMES[address[1]][-1]['WIDTH'], FRAMES[address[1]][-1]['HEIGHT'])

            #if not recording:
                # No longer recording. Throw away all but last few FRAMES
                #temp_frames = FRAMES[address[1]]
                #temp_frames = temp_frames[(len(temp_frames) - (data['FPS'] * SECONDS)):]
                #FRAMES[address[1]] = temp_frames
                #print('Video saved to', output_file)


        # Write the latest frame to a file called <client id><a/b>.jpg, which will then be used by flask server
        # Example: flask webserver reads 1b while 1a is being written to.
        # This is not the most efficient way of streaming, but it provides a smooth stream.
        #name = 'a' if alternator else 'b'
        #filename = 'stream_frames/{}{}.jpg'.format(helper.getClientCount(), name)
        #alternator = not alternator # alternate between two frames
        #cv.imwrite(filename, processed_frame)

        # Save which image was most recently output (a or b)
        #with open('stream_frames/{}.txt'.format(helper.getClientCount()), 'w') as file:
             #file.write(name)

        cv.imshow('Client: {} ({})'.format(address[1], address[0]), processed_frame)
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
        helper.updateClientCount(helper.getClientCount() + 1)

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
        helper.updateClientCount(0) # Ensure that server knows no clients are connected when it restarts. (Connection will be re-established)

        # TODO: move this back to main if necessary, and remove when done developing
        # Close server connection
        cv.destroyAllWindows()
