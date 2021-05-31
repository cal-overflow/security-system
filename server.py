from multiprocessing import Process as process
import cv2 as cv
import socket
import pickle
import datetime, time
import os, sys
from decouple import config as ENV
import systemhelper as helper

HOST = '0.0.0.0'
PORT = 8080
CLIENTS = []
PROCESSES = []
FRAMES = {}
MAX_CLIENTS = int(ENV('MAX_CLIENTS'))

def stream_camera(client, address, id):
    '''Stream video from a client'''

    # Do not stream this camera if there are more than 5 devices connected
    clientCount = helper.getClientCount()
    if clientCount > MAX_CLIENTS:
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
        if len(temp_frames) > data['FPS'] * int(ENV('SECONDS')) and not recording:
            temp_frames.pop(0)
        FRAMES[address[1]] = temp_frames

        # Process the frame (add timestamp(), handle recording), and update FRAMES, if necessary
        processed_frame, recording, temp_frames = processFrame(data, address, id, recording, FRAMES)
        if temp_frames is not None:
            FRAMES[address[1]] = temp_frames

        # Write every other frame to file for webserver to stream.
        # (Alternating makes the stream smoother, since file is not locked and being written to as much)
        if alternator:
            writeToFile(id, processed_frame)
        alternator = not alternator

        cv.waitKey(10)

def processFrame(data, address, id, recording, FRAMES):
    '''Process the frame. Handle recording and alert decisions.'''
    # Handle recording behavior
    # If there is motion in this frame or there was recently motion (and it is recording), then act accordingly
    # Ignore if this is the first frame sent from client
    if (data['MOTION'] and len(FRAMES[address[1]]) != 1) or recording:
        if (helper.getStatus() == 'on') and not recording:
            alert(id) # Alert when motion (recording) first starts and alerts are enabled

        recording, output_file = record(FRAMES[address[1]], recording, int(ENV('SECONDS')), id)
        processed_frame = helper.drawRecording(data['FRAME'], data['WIDTH'], data['HEIGHT'])


        if not recording:
            # No longer recording. Throw away all but last few FRAMES
            temp_frames = FRAMES[address[1]]
            temp_frames = temp_frames[(len(temp_frames) - (data['FPS'] * int(ENV('SECONDS')))):]
            if output_file is not None:
                print('{} [SERVER]: Video recording saved to {}'.format(helper.timestamp(), output_file))
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

def record(frames, already_recording, SECONDS, id):
    '''Record video when motion is detected. Includes the few seconds prior to motion detection and few seconds after the motion stops.'''
    FPS = frames[0]['FPS']
    WIDTH = frames[0]['WIDTH']
    HEIGHT = frames[0]['HEIGHT']
    motion = []

    for frame in frames:
        motion.append(frame['MOTION'])

    # Check if there has been motion in the last few seconds
    start = len(motion) - (FPS * SECONDS)
    # If the start index is less than 0, then default to True.
    movement_lately = True if (start < 0 or (True in motion[start:])) else False
    output_file = None

    if not movement_lately:
        #stop the recording. Write to a video file
        print('{} [SERVER]: Saving recording from Client {} '.format(helper.timestamp(), id))

        # Ensure that user has a correct video type
        if ENV('RECORDING_TYPE') == 'mp4':
            fourcc = cv.VideoWriter_fourcc(*'mp4v')
        elif ENV('RECORDING_TYPE') == 'avi':
            fourcc = cv.VideoWriter_fourcc(*'XVID')
        else:
            print('{} [SERVER]: Can not record video of type: {}\nChange the RECORDING_TYPE to one of the acceptable video types (listed under step 2a on README) in your .env and restart the server to enable video recordings to be saved'.format(helper.timestamp(), ENV('RECORDING_TYPE')))
            return False, None

        output_file = "static/recordings/{}CAM{}.{}".format(datetime.datetime.now().strftime("%m-%d-%Y/%H_%M_%S"), id, ENV('RECORDING_TYPE'))
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        open(output_file, 'a+').close()
        output = cv.VideoWriter(output_file, fourcc, FPS, (WIDTH, HEIGHT), True)

        for frame in frames:
            output.write(helper.drawRecording(frame['FRAME'], WIDTH, HEIGHT))

        output.release() # Completed writing to output file

    return movement_lately, output_file

def alert(id):

    '''Notify (via email) that motion has been detected.'''
    gmail_user = ENV('GMAIL_USER')
    gmail_password = ENV('GMAIL_APP_PASSWORD')

    sent_from = gmail_user
    to = [] # Email recipients here
    subject = 'ALERT - Security System'
    body = 'ALERT: Movement has been detected by the security system on {} by camera {}'.format(datetime.datetime.now().strftime("%d/%m/%Y at %H:%M:%S"), id)

    email_text = """\
    From: %s
    To: %s
    Subject: %s

    %s
    """ % (sent_from, ", ".join(to), subject, body)

    if len(to) == 0:
        return
    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.ehlo()
        server.login(gmail_user, gmail_password)
        server.sendmail(sent_from, to, email_text)
        server.close()

        print('{} [SERVER]: Movement detected. Alerts successfully sent.'.format(helper.timestamp()))
    except:
        print('{} [SERVER]: There was an issue sending alerts.'.format(helper.timestamp()))

def disconnect(client, address, FRAMES, id):
    '''Handle client disconnection'''
    print('{} [SERVER]: Socket {} (client {}) disconnected'.format(helper.timestamp(), address[1], id))
    helper.setStandby(id) # Set standby image as frame
    client.close()

    # Remove this process from PROCESSES and update client count
    # TODO: #PROCESSES.pop(id - 1) # camera 3 is index 2 (3rd process) # TODO: see if this works
    FRAMES.pop(address[1], None)
    helper.updateClientCount(helper.getClientCount() - 1)

def main():
    print('{} [SERVER]: Server running on port {}'.format(helper.timestamp(), PORT))

    # Create Server (socket) and bind it to a address/port.
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(MAX_CLIENTS)
    print('{} [SERVER]: Listening for (client) sockets'.format(helper.timestamp()))

    while True:
        # Accept client connection
        client, address = server.accept()
        client.settimeout(5.0)

        if helper.isBlacklisted(address[0]) or helper.getClientCount() == MAX_CLIENTS:
            # Close connection since they are blacklisted or
            # there are already the max number of clients connected.
            print('{} [SERVER]: Blacklisted IP {} attempted to connect'.format(helper.timestamp(), address[0]))
            client.close()
            continue # Wait for next client

        # Only continue with this client if they send a confirmation message.
        # This is sort of a second handshake before the client establishes a video stream to server.
        try:
            confirmation = client.recv(1024).decode() # Client should be sending confirmation
        except (socket.timeout, UnicodeDecodeError):
            # Client did not send decodable confirmation in time. Add them to the blacklist if they are unrecognized.
            if not helper.isWhitelisted(address[0]):
                helper.addToBlackList(address[0])
                print('{} [SERVER]: IP {} has been blacklisted for failing to confirm the connection'.format(helper.timestamp(), address[0]))
                client.close()
                continue # Wait for next client

        # Whitelist client IP, since they connected successfully.
        helper.addToWhiteList(address[0])

        # Begin a process for this client's video stream
        helper.updateClientCount(helper.getClientCount() + 1)
        print('{} [SERVER]: Socket {} connected as client {}'.format(helper.timestamp(), address, helper.getClientCount()))

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
        except Exception as e:
            print(e)
            print('{} [SERVER]: Server crashed'.format(helper.timestamp()))

            time.sleep(5)
            print('{} [SERVER]: Restarting server'.format(helper.timestamp()))
