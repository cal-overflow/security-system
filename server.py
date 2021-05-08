from multiprocessing import Process as process
import cv2 as cv
import socket
import pickle
import datetime, time
import systemhelper as helper

HOST = '0.0.0.0'
PORT = 8080
CLIENTS = []
PROCESSES = []
FRAMES = {}

def stream_camera(client, address, id):
    '''Stream video from a client'''

    # Do not stream this camera if there are more than 5 devices connected
    clientCount = helper.getClientCount()
    if clientCount > helper.MAX_CLIENTS:
        return

    FRAMES[address[1]] = [] # This client has no previously saved frames (for recording)
    encoded_data, message_size, msg_size = b'', None, None
    recording = False # Not recoridng when stream begins
    alternator = True

    # Continuous streaming
    while True:
        client.settimeout(None)

        # Change this camera's id when any preceding cameras disconnect (ie., when camera 3 disconnects, camera 4 takes its place as camera 3)
        #print(id, '>=', helper.getClientCount(), ' and ', helper.getClientCount(), '<', clientCount)
        if id >= helper.getClientCount() and helper.getClientCount() < clientCount:
            print('client {} became client {}'.format(id, id - 1))
            print('helper.getClientCount(): {}\n clientCount: {}'.format(helper.getClientCount(), clientCount))
            id -= 1 if (id != 1) else 0
            clientCount -= 1 if (id != 1) else 0
        elif clientCount < helper.getClientCount():
            clientCount = helper.getClientCount()

        # Recieve encoded_data stream from socket (client)
        while len(encoded_data) < helper.PACKAGE_SIZE:
            received = client.recv(4096)

            if not received:
                # Disconnect since client sent nnothing. Exit function
                disconnect(client, address, FRAMES, id)
                return

            else:
                encoded_data += received

        # Determine the size of the incoming message and receive it
        message_size = encoded_data[:helper.PACKAGE_SIZE]
        encoded_data = encoded_data[helper.PACKAGE_SIZE:]
        msg_size = helper.struct.unpack("P", message_size)[0]

        while len(encoded_data) < msg_size:
            try:
                encoded_data += client.recv(4096)
            except Exception as e:
                # Issues receiving data from client. Disconnect and exit function.
                disconnect(client, address, FRAMES, id)
                return

        # Store and decode the encoded data
        pickled_data = encoded_data[:msg_size]
        encoded_data = encoded_data[msg_size:]
        data = pickle.loads(pickled_data)

        # Update frames (for recording)
        temp_frames = FRAMES[address[1]]
        temp_frames.append(data)
        if len(temp_frames) > data['FPS'] * helper.SECONDS and not recording:
            temp_frames.pop(0)
        FRAMES[address[1]] = temp_frames

        # Process the frame (add timestamp, handle recording), and update FRAMES, if necessary
        processed_frame, recording, temp_frames = processFrame(data, address, id, recording, FRAMES)
        if temp_frames is not None:
            FRAMES[address[1]] = temp_frames

        # Write every other frame to file for webserver to stream.
        # (Alternating makes the stream smoother, since file is not locked and being written to as much)
        if alternator:
            writeToFile(id, processed_frame)
        alternator = not alternator

        #cv.imshow('Client: {} ({})'.format(id, address[0]), processed_frame) # TODO: delete this. dev purposes only
        cv.waitKey(10)

def processFrame(data, address, id, recording, FRAMES):
    '''Process the frame. Handle recording and alert decisions.'''
    # Handle recording behavior
    # If there is motion in this frame or there was recently motion (and it is recording), then act accordingly
    # Ignore if this is the first frame sent from client
    if (data['MOTION'] and len(FRAMES[address[1]]) != 1) or recording:
        if (helper.getStatus() == 'on') and not recording:
            # Alert status is 'on' and recording just began. Send ALERT
            helper.alert(id)

        # TODO: UNCOMMENT!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! # TODO!!!!
        #recording, output_file = helper.record(FRAMES[address[1]], recording, id)
        processed_frame = helper.drawRecording(data['FRAME'], data['WIDTH'], data['HEIGHT'])

        recording = False # TODO: DELETE!!!!!!!!!!!!!!!! # TODO!!!!!!
        if not recording:
            # No longer recording. Throw away all but last few FRAMES
            temp_frames = FRAMES[address[1]]
            temp_frames = temp_frames[(len(temp_frames) - (data['FPS'] * helper.SECONDS)):]
            #print('{} [INFO]: Video recording saved to {}'.format(helper.TIMESTAMP, output_file)) # TODO: uncomment

        else:
            temp_frames = None
    else:
        processed_frame = data['FRAME']
        temp_frames = None

    return processed_frame, recording, temp_frames

def writeToFile(id, frame):
    '''Lock the frame file and write the current (most recently received) frame to it. Then unlock frame so webserver can access frame.'''
    if helper.readLock(id) == 'unlocked':
        helper.lock(id)
        filename = 'data/stream_frames/{}/frame.jpg'.format(id)

        cv.imwrite(filename, frame)
        helper.unlock(id)

def disconnect(client, address, FRAMES, id):
    '''Handle client disconnection'''
    print('{} [INFO]: Socket {} (client {}) disconnected'.format(helper.TIMESTAMP, address[1], id))
    helper.setStandby(id) # Set standby image as frame
    client.close()

    # Remove this process from PROCESSES and update client count
    # TODO: #PROCESSES.pop(id - 1) # camera 3 is index 2 (3rd process) # TODO: see if this works
    FRAMES.pop(address[1], None)
    helper.updateClientCount(helper.getClientCount() - 1)

def main():
    print('{} [INFO]: Server running'.format(helper.TIMESTAMP))

    # Create Server (socket) and bind it to a address/port.
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(helper.MAX_CLIENTS)
    print('{} [INFO]: Listening for (client) sockets'.format(helper.TIMESTAMP))

    while True:
        # Accept connection
        client, address = server.accept()
        client.settimeout(5.0)

        if helper.isBlacklisted(address[0]) or helper.getClientCount() == helper.MAX_CLIENTS:
            # Close connection since they are blacklisted or
            # there are already the max number of clients connected.
            print('Blacklisted IP', address[0], 'attempted to connect')
            client.close()
            continue # Wait for next client

        # Only continue with this client if they send a confirmation message.
        # This is sort of a second handshake before the client establishes a video stream to server.
        try:
            confirmation = client.recv(1024).decode() # Client should be sending confirmation
        except (socket.timeout, UnicodeDecodeError):
            # Client did not send decodable confirmation in time. Disconnect them.
            helper.addToBlackList(address[0])
            print('IP', address[0], ' has been blacklisted for failing to confirm connection')
            client.close()
            continue # Wait for next client

        # Begin a process for this client's video stream
        helper.updateClientCount(helper.getClientCount() + 1)
        print('{} [INFO]: Socket {} connected as client {}'.format(helper.TIMESTAMP, address, helper.getClientCount()))

        # Create, save, and start process (camera stream)
        p = process(target=stream_camera, args=(client, address, helper.getClientCount(), ))
        PROCESSES.append(p)
        p.start()

    # Clear PROCESSES
    for p in PROCESSES:
        p.join() # Join all PROCESSES

    socket.close() # TODO: see if this should be server.close() instead

if __name__ == '__main__':
    while True:
        try:
            helper.toggleStatus('on') # Set alert status to 'on' by default
            helper.updateClientCount(0) # No clients can be connected on startup. (Connection will be re-established)
            # Set each client default frame and lock to 'unlocked'
            standby = cv.imread('static/standby.jpg', cv.IMREAD_UNCHANGED)
            for i in range(1, 4):
                helper.unlock(i) # Unlock all frames for next server instance
                #with open('data/stream_frames/{}/frame.jpg'.format(i), 'r') as file:
                cv.imwrite('data/stream_frames/{}/frame.jpg'.format(i), standby)

            main()
        except:
            print('{} [INFO]: Server crashed'.format(helper.TIMESTAMP))

            time.sleep(5)
            print('{} [INFO]: Restarting server'.format(helper.TIMESTAMP))
