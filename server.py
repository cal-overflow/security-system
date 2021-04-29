import cv2 as cv
import sys
import socket
from socketserver import ThreadingMixIn
import pickle
import struct
import time
from multiprocessing import Process as process
import threading
import functions as helper
from _thread import *

HOST = '0.0.0.0'
#HOST = '127.0.0.1'
PORT = 8000
MAX_CLIENTS = 5
SECONDS = 10
#CLIENTS = []
#PROCESSES = []
FRAMES = {}

#threading.set_allow_shutdown(True) # TODO: delete
# TODO: rename class
class ClientThread(threading.Thread):
    def __init__(self, client, address):
        threading.Thread.__init__(self)
        self.client = client
        self.address = address
        print('New server socket thread started for client', address)

    # TODO: see if this can be renamed to stream_camera
    #def run(self, client, address):
    def run(self):
        '''Stream video from a client'''
        id = helper.getClientCount()
        print('streaming camera:', id)

        alternator = True
        FRAMES[self.address[1]] = [] # This client has no previously saved frames (for recording)
        package_size = struct.calcsize("P")
        encoded_data, message_size, msg_size = b'', None, None
        recording = False # Not recoridng when stream begins

        # Continuous streaming
        while True:
            if id != 1:
                print('acquiring lock', id)
            with threading.Lock():
                if id != 1:
                    print('lock acquired', id)
                # Change this camera's id when any preceding cameras disconnect (ie., when camera 3 disconnects, camera 4 takes its place as camera 3)
                if id > helper.getClientCount():
                    id -= 1

                # Recieve encoded_data stream from socket (client)
                while len(encoded_data) < package_size:
                    received = self.client.recv(4096)

                    if not received:
                        # Close connection since nothing was received (client is no longer communicating)
                        self.client.close()
                        print('Socket {} disconnected'.format(self.address[1]))
                        #PROCESSES.pop(id - 1) # camera 3 is index 2 (3rd process) # TODO: see if this works
                        FRAMES.pop(self.address[1], None)
                        helper.updateClientCount(helper.getClientCount() - 1)
                        print(helper.getClientCount())
                        return # exit stream_camera function

                    else:
                        encoded_data += received

                # Determine the size of the incoming message and receive it
                message_size = encoded_data[:package_size]
                encoded_data = encoded_data[package_size:]
                msg_size = struct.unpack("P", message_size)[0]

                while len(encoded_data) < msg_size:
                    encoded_data += self.client.recv(4096)

                # Store and decode the encoded data
                pickled_data = encoded_data[:msg_size]
                encoded_data = encoded_data[msg_size:]
                data = pickle.loads(pickled_data)

                # Update frames (for recording)
                temp_frames = FRAMES[self.address[1]]
                temp_frames.append(data)
                if len(temp_frames) > data['FPS'] * SECONDS and not recording:
                    temp_frames.pop(0)
                FRAMES[self.address[1]] = temp_frames

                processed_frame = FRAMES[self.address[1]][-1]['FRAME']

                # Handle recording behavior
                # If there is motion in this frame or there was recently motion (and it is recording), then act accordingly
                #if data['MOTION'] or recording:
                    #recording, output_file = helper.record(FRAMES[address[1]], recording, SECONDS, id)
                    #processed_frame = helper.drawRecording(FRAMES[address[1]][-1]['FRAME'], FRAMES[address[1]][-1]['WIDTH'], FRAMES[address[1]][-1]['HEIGHT'])

                    #if not recording:
                        # No longer recording. Throw away all but last few FRAMES
                        #temp_frames = FRAMES[address[1]]
                        #temp_frames = temp_frames[(len(temp_frames) - (data['FPS'] * SECONDS)):]
                        #FRAMES[address[1]] = temp_frames
                        #print('Video saved to', output_file)


                # Write the latest frame to a file called <camera id><a/b>.jpg, which will then be used by flask server
                # Example: flask webserver reads 1b while 1a is being written to.
                # This is probably NOT the most efficient way of streaming, but it provides a fairly smooth stream.
                name = 'a' if alternator else 'b'
                filename = 'stream_frames/{}{}.jpg'.format(id, name)
                alternator = not alternator # alternate (writing to) frames
                cv.imwrite(filename, processed_frame)

                # Save which image was most recently output (a or b)
                with open('stream_frames/{}.txt'.format(helper.getClientCount()), 'w') as file:
                     file.write(name)

                # TODO: RESTORE
                #cv.imshow('streamed video', frame)
                cv.imshow('Client: {} ({})'.format(id, self.address[0]), processed_frame)
                print('frame received from Client {}'.format(id))
                cv.waitKey(1)
                time.sleep(.01) # TODO: remove

def main():
    sys.setswitchinterval(.5) # TODO: REMOVE!
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))

    #lock = threading.Lock()
    THREADS = []

    print('Listening for sockets')

    while True:
        server.listen(MAX_CLIENTS)
        # Accept connection
        client, address = server.accept()
        print('Socket Connection:', address) # TODO: delete
        helper.updateClientCount(helper.getClientCount() + 1)

        t = ClientThread(client, address)
        t.start()
        THREADS.append(t)

    for t in THREADS:
        t.join()

if __name__ == '__main__':
    try:
        main()
    except:
        helper.updateClientCount(0) # Ensure that server knows no clients are connected when it restarts. (Connection will be re-established)

        # Close server connection
        cv.destroyAllWindows() # TODO: Delete
