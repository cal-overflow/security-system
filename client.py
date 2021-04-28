import cv2 as cv
import socket
import pickle
import struct
import time
import datetime
import functions as helper

#HOST = '192.168.0.8' # Server address
#HOST = '127.0.0.1'
HOST = '0.0.0.0'
#HOST = '192.168.0.34'
PORT = 8000

def main():
    '''Client that connects and streams video to server.'''

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.connect((HOST, PORT))

    print('{} [INFO]: Established connection with server'.format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    FPS = helper.getFPS()

    print('{} [INFO]: Calibrating camera (retreiving FPS)'.format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    camera = cv.VideoCapture(0)
    if not camera.isOpened():
        # Attempt to open capture device once more, after a failure
        camera.open()
        if not camera.isOpened():
            print('{} [INFO]: Issue opening camera'.format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            exit()

    print('{} [INFO]: Beginning stream to server'.format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    ret, frame1 = camera.read()
    ret, frame2 = camera.read()
    connection_failed = False

    while camera.isOpened():
        detected_motion, motion_frame = helper.detectMotion(frame1, frame2, int(camera.get(3)), int(camera.get(4)))
        frame = helper.drawTime(motion_frame, int(camera.get(3)), int(camera.get(4)))
        data = {'FRAME': frame,
                'MOTION': detected_motion,
                'FPS': FPS,
                'WIDTH': int(camera.get(3)),
                'HEIGHT': int(camera.get(4))
                }
        pickled_data = pickle.dumps(data)

        #pickled_data = pickle.dumps(frame) # TODO: delete
        #server.sendall(struct.pack("P", len(pickled_data))+pickled_data) # TODO: delete
        try:
            server.sendall(struct.pack("P", len(pickled_data))+pickled_data)

        # Handle connection issues
        except socket.error:
            print('{} [INFO]: Connection to server disrupted'.format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            connected = False
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            # Try to reconnect
            while not connected:
                try:
                    server.connect((HOST, PORT))
                    connected = True
                    if connection_failed:
                        # Connection was re-established after it recently failed
                        print('{} [INFO]: Re-established connection with server'.format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                        connection_failed = False
                except socket.error:
                    connected = False
                    connection_failed = True
                    camera.release()
                    time.sleep(5) # Wait 5 seconds before trying to reconnect
                    print('{} [INFO]: Attempting to re-establish connection with server'.format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                    camera.open(0)

        #cv.imshow('frame', frame1) # TODO: delete
        frame1 = frame2
        ret, frame2 = camera.read()
        cv.waitKey(1)

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        cv.destroyAllWindows() # TODO: delete
        print('{}[INFO]: Exiting Script because of error. Cause: {}'.format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), e))

#helpful resources:
#https://stackoverflow.com/questions/30988033/sending-live-video-frame-over-network-in-python-opencv#
#https://stackoverflow.com/questions/53347759/importerror-libcblas-so-3-cannot-open-shared-object-file-no-such-file-or-dire
#https://stackoverflow.com/questions/54665842/when-importing-tensorflow-i-get-the-following-error-no-module-named-numpy-cor
#https://stackoverflow.com/questions/34051737/numpy-core-multiarray-failed-to-import
#https://stackoverflow.com/questions/10810249/python-socket-multiple-clients
#https://instructobit.com/tutorial/101/Reconnect-a-Python-socket-after-it-has-lost-its-connection
