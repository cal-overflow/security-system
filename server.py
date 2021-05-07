import cv2 as cv
import socket
import pickle
import struct
import time
import datetime
from multiprocessing import Process as process
import functions as helper

HOST = '0.0.0.0'
#HOST = '127.0.0.1'
PORT = 8080
MAX_CLIENTS = 5
SECONDS = 10
CLIENTS = []
PROCESSES = []
FRAMES = {}

def stream_camera(client, address, id):
    '''Stream video from a client'''

    # Do not stream this camera if there are more than 5 devices connected
    if helper.getClientCount() > 5:
        return

    alpha_index = 0 # Index of which frame is being written (a, b, c, ...). Important for webserver displaying full images
    FRAMES[address[1]] = [] # This client has no previously saved frames (for recording)
    package_size = struct.calcsize("P")
    encoded_data, message_size, msg_size = b'', None, None
    recording = False # Not recoridng when stream begins

    # Continuous streaming
    while True:
        # Change this camera's id when any preceding cameras disconnect (ie., when camera 3 disconnects, camera 4 takes its place as camera 3)
        if id > helper.getClientCount():
            id -= 1

        # Recieve encoded_data stream from socket (client)
        while len(encoded_data) < package_size:
            received = client.recv(4096)

            if not received:
                # Close connection since nothing was received (client is no longer communicating)
                client.close()
                print('{} [INFO]: Socket {} (client {}) disconnected'.format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), address[1], id))
                #PROCESSES.pop(id - 1) # camera 3 is index 2 (3rd process) # TODO: see if this works
                FRAMES.pop(address[1], None)
                helper.updateClientCount(helper.getClientCount() - 1)
                return # exit stream_camera function

            else:
                encoded_data += received

        # Determine the size of the incoming message and receive it
        message_size = encoded_data[:package_size]
        encoded_data = encoded_data[package_size:]
        msg_size = struct.unpack("P", message_size)[0]

        while len(encoded_data) < msg_size:
            encoded_data += client.recv(4096)

        # Store and decode the encoded data
        pickled_data = encoded_data[:msg_size]
        encoded_data = encoded_data[msg_size:]
        data = pickle.loads(pickled_data)

        # Update frames (for recording)
        temp_frames = FRAMES[address[1]]
        temp_frames.append(data)
        if len(temp_frames) > data['FPS'] * SECONDS and not recording:
            temp_frames.pop(0)
        FRAMES[address[1]] = temp_frames

        # Process the frame from 10 seconds ago
        #if len(FRAMES[address[1]]) < data['FPS'] * SECONDS:
            #processed_frame = FRAMES[address[1]][0]['FRAME']
        #else:
            #processed_frame = FRAMES[address[1]][(len(FRAMES[address[1]]) - (data['FPS'] * SECONDS))]['FRAME']
        processed_frame = FRAMES[address[1]][-1]['FRAME']

        # Handle recording behavior
        # If there is motion in this frame or there was recently motion (and it is recording), then act accordingly
        # Ignore if this is the first frame sent from client
        if (data['MOTION'] and len(FRAMES[address[1]]) != 1) or recording:
            if (helper.getStatus() == 'on') and not recording:
                # Alert status is 'on' and recording just began. Send ALERT
                helper.alert(id)
                recording = True # TODO: DELETE
            recording, output_file = helper.record(FRAMES[address[1]], recording, SECONDS, id)
            processed_frame = helper.drawRecording(FRAMES[address[1]][-1]['FRAME'], FRAMES[address[1]][-1]['WIDTH'], FRAMES[address[1]][-1]['HEIGHT'])

            if not recording:
                # No longer recording. Throw away all but last few FRAMES
                temp_frames = FRAMES[address[1]]
                temp_frames = temp_frames[(len(temp_frames) - (data['FPS'] * SECONDS)):]
                FRAMES[address[1]] = temp_frames
                print('{} [INFO]: Video recording saved to {}'.format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), output_file))


        # Write the latest frame to a file called <camera id><alpha character>.jpg, which will then be used by flask server
        # Example: flask webserver reads 1b while 1a is being written to.
        # This is NOT the most efficient way of streaming, but it provides a fairly smooth stream.
        letter = helper.ALPHA[alpha_index]

        # Save which alpha index was most recently output (a, b, c, ...)
        with open('data/stream_frames/{}.txt'.format(helper.getClientCount()), 'w') as file:
             file.write(helper.ALPHA[alpha_index - 1]) # Write down previous frame (that will have been completed)

        alpha_index = alpha_index + 1 if (alpha_index + 1 < len(helper.ALPHA)) else 0

        filename = 'data/stream_frames/{}{}.jpg'.format(id, letter)
        cv.imwrite(filename, processed_frame)

        #cv.imshow('Client: {} ({})'.format(id, address[0]), processed_frame) # TODO: delete this. dev purposes only

        cv.waitKey(100)

def main():
    print('{} [INFO]: Server running'.format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

    # Create Server (socket) and bind it to a address/port.
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(MAX_CLIENTS)
    print('{} [INFO]: Listening for (client) sockets'.format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

    while True:
        # Accept connection
        client, address = server.accept()
        helper.updateClientCount(helper.getClientCount() + 1)
        print('{} [INFO]: Socket {} connected as client {}'.format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), address, helper.getClientCount()))

        # Create, save, and start process (camera stream)
        p = process(target=stream_camera, args=(client, address, helper.getClientCount(), ))
        PROCESSES.append(p)
        p.start()

    # Clear PROCESSES
    for p in PROCESSES:
        p.join() # Join all PROCESSES

    socket.close() # TODO: see if this should be server.close() instead

if __name__ == '__main__':
    # TODO: determine if I want this in a while loop or not
    while True:
        try:
            main()
        except:
            helper.toggleStatus('on') # Set alert status to 'on' by default
            helper.updateClientCount(0) # Ensure that server knows no clients are connected when it restarts. (Connection will be re-established)

            print('{} [INFO]: Server crashed'.format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            time.sleep(5)
            print('{} [INFO]: Restarting server'.format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

            # TODO: move this back to main if necessary, and remove when done developing (won't have cv windows)
            # Close server connection
            #cv.destroyAllWindows()
