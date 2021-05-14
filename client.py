import cv2 as cv
import socket
import pickle
import time
import datetime
import systemhelper as helper

#HOST = '192.168.0.8' # Server address
#HOST = '127.0.0.1'
HOST = '18.222.112.110'
#HOST = '192.168.0.9'
PORT = 8080

def main():
    '''Client that connects and streams video to server.'''

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.connect((HOST, PORT))

    confirmRelationship(server)
    print('{} [CLIENT]: Established connection with server'.format(helper.TIMESTAMP))

    # Set and calibrate camera
    camera, FPS = helper.calibrateCamera()

    print('{} [CLIENT]: Beginning stream to server'.format(helper.TIMESTAMP))
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
        #server.sendall(helper.struct.pack("P", len(pickled_data))+pickled_data) # TODO: delete
        try:
            server.sendall(helper.struct.pack("P", len(pickled_data))+pickled_data)
        # Handle connection issues
        except socket.error:
            print('{} [CLIENT]: Connection to server disrupted'.format(helper.TIMESTAMP))
            connected = False
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            # Try to reconnect
            while not connected:
                try:
                    server.connect((HOST, PORT))
                    confirmRelationship(server)
                    connected = True
                    if connection_failed:
                        # Connection was re-established after it recently failed
                        print('{} [CLIENT]: Re-established connection with server'.format(helper.TIMESTAMP))
                        connection_failed = False
                except socket.error:
                    connected = False
                    connection_failed = True
                    camera.release()
                    time.sleep(2.5) # Wait 5 seconds before trying to reconnect
                    print('{} [CLIENT]: Attempting to re-establish connection with server'.format(helper.TIMESTAMP))
                    camera.open(0)

        #cv.imshow('frame', frame1) # TODO: delete
        frame1 = frame2
        ret, frame2 = camera.read()
        cv.waitKey(1)

def confirmRelationship(server):
    '''Confirm relationship with server. This acts as an extra
    handshake that must be made between client and server.'''
    server.send(b'confirmation')

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        cv.destroyAllWindows() # TODO: delete
        print('{}[CLIENT]: Exiting Script because of error. Cause: {}'.format(helper.TIMESTAMP, e))
