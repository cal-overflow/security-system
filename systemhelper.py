# Helpful functions and constants used by webserver, server, and client scripts
import cv2 as cv
import smtplib
import struct
from pathlib import Path
import os, datetime, time, math
from decouple import config as ENV

###############################################
# CONSTANTS
###############################################

THRESHOLD = 10000 # Movement detection threshold
STANDBY_FRAME = cv.imread('static/standby.jpg', cv.IMREAD_UNCHANGED)
PACKAGE_SIZE = struct.calcsize("P")
MAX_CLIENTS = int(ENV('MAX_CLIENTS'))
SECONDS = int(ENV('SECONDS'))
TIMESTAMP = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
RECORDING_TYPE = ENV('RECORDING_TYPE')

###############################################
# HELPER FUNCTIONS
###############################################

def record(frames, already_recording, id):
    '''Record video when motion is detected. Includes the few seconds prior to motion detection and few seconds after the motion stops.'''
    FPS = frames[0]['FPS']
    WIDTH = frames[0]['WIDTH']
    HEIGHT = frames[0]['HEIGHT']
    motion = []

    for frame in frames:
        #print(frame)
        motion.append(frame['MOTION'])

    # Check if there has been motion in the last few seconds
    start = len(motion) - (FPS * SECONDS)
    # If the start index is less than 0, then default to True.
    movement_lately = True if (start < 0 or (True in motion[start:])) else False
    output_file = None

    if not movement_lately:
        #stop the recording. Write to a video file
        print('writing recording to file')

        # Ensure that user has the correct video type
        if RECORDING_TYPE == 'mp4':
            fourcc = cv.VideoWriter_fourcc(*'FMP4')
        elif RECORDING_TYPE == 'avi':
            fourcc = cv.VideoWriter_fourcc(*'XVID')
        else:
            print('{} [SERVER]: Can not record video of type: {}\nChange the RECORDING_TYPE to one of the acceptable video types (listed under step 2a on README) in your .env and restart the server to enable video recordings to be saved'.format(TIMESTAMP, RECORDING_TYPE))
            return False, None

        output_file = "static/recordings/{}CAM{}.{}".format(datetime.datetime.now().strftime("%m-%d-%Y/%H_%M_%S"), id, RECORDING_TYPE)
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        open(output_file, 'a+').close()
        output = cv.VideoWriter(output_file, fourcc, FPS, (WIDTH, HEIGHT), True)

        for frame in frames:
            output.write(drawRecording(frame['FRAME'], WIDTH, HEIGHT))

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

    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.ehlo()
        server.login(gmail_user, gmail_password)
        server.sendmail(sent_from, to, email_text)
        server.close()

        print('Movement detected. Alerts successfully sent.')
    except:
        print('There was an issue sending alerts.')

def calibrateCamera():
    '''Calibrate the camera. Get the true FPS (including processing) from the camera'''
    print('{} [CLIENT]: Calibrating camera'.format(TIMESTAMP))
    camera = cv.VideoCapture(0)
    width = camera.get(cv.CAP_PROP_FRAME_WIDTH)
    height = camera.get(cv.CAP_PROP_FRAME_HEIGHT)

    # Adjust frame size if it is excessively large
    while width * height  >= 1000000:
        width *= 0.75
        height *= 0.75

    # OpenCV will override input and round to the closest (recognized) resolution. For example, I set res to 1900x1070 and it will override as 1920x1080.
    camera.set(3, width)
    camera.set(4, height)

    if not camera.isOpened():
        # Attempt to open capture device once more, after a failure
        camera.open()
        if not camera.isOpened():
            print('{} [CLIENT]: Issue opening camera'.format(TIMESTAMP))
            exit()

    start_time = time.time()
    count = 0
    while int(time.time() - start_time) < 10:
        ret, frame = camera.read()
        count += 1 # number of frames

    return camera, int(count / 10)

def detectMotion(f1, f2, WIDTH, HEIGHT):
    '''Detect motion given two frames. Returns boolean and frame with motion area outlined.'''
    # Helpful Source: Divyanshu Shekhar - https://divyanshushekhar.com/motion-detection-opencv/
    difference = cv.absdiff(f1, f2)
    gray_difference = cv.cvtColor(difference, cv.COLOR_BGR2GRAY)
    blur = cv.GaussianBlur(gray_difference, (5, 5), 0)
    __, thresh = cv.threshold(blur, 20, 255, cv.THRESH_BINARY)
    dilated = cv.dilate(thresh, None, iterations=3)
    contours, __ = cv.findContours(dilated, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)

    detected = False
    frame = f1.copy()
    for contour in contours:

        (x, y, w, h) = cv.boundingRect(contour)
        # Place date on frame regardless of any movement
        if cv.contourArea(contour) >= THRESHOLD:
            detected = True

            cv.rectangle(frame, (x, y), (x+w, y+h), (255, 255, 255), 1)
            cv.putText(frame, 'MOTION', (10, 20), cv.FONT_HERSHEY_PLAIN, 1.25, (0, 0, 224), 2, cv.FILLED, False)

    return detected, frame

def drawTime(frame, WIDTH, HEIGHT):
    '''Draw the date/time on the given frame.'''
    cv.putText(frame, datetime.datetime.now().strftime("%c"), (10, HEIGHT - 10), cv.FONT_HERSHEY_PLAIN, 1, (255, 255, 255), 2, cv.FILLED, False)
    return frame

def drawRecording(frame, WIDTH, HEIGHT):
    '''Draw a recording message on the given frame'''
    text = 'RECORDING' if (int(time.time()) % 2 == 0) else ''
    cv.putText(frame, text, (WIDTH - 140, 20), cv.FONT_HERSHEY_PLAIN, 1.25, (0, 0, 224), 2, cv.FILLED, False)
    return frame

def getClientCount():
    '''Return the current number of clients'''
    with open('data/clients.txt', 'r') as file:
        count = int(file.read())
    #print('Client count:', count) # TODO: delete
    return count

def updateClientCount(i):
    '''Update number of clients'''
    with open('data/clients.txt', 'w+') as file:
        file.write(str(i))

def getStatus():
    '''Get the alarm status'''
    with open('data/alarm_status.txt', 'r') as file:
        status = file.read()
    return status.strip('\n')

def toggleStatus(init=None):
    '''Toggle the status of the alarm (on or off)'''
    if init:
        new = init
    else:
        old = getStatus()
        new = 'on' if (old == 'off') else 'off'

    with open('data/alarm_status.txt', 'w+') as file:
        file.write(new)

    return new

def unlock(id):
    with open('data/stream_frames/{}/lock.txt'.format(id), 'w+') as file:
        file.write('unlocked')

def lock(id):
    with open('data/stream_frames/{}/lock.txt'.format(id), 'w+') as file:
        file.write('locked')

def readLock(id):
    with open('data/stream_frames/{}/lock.txt'.format(id), 'r') as file:
        return file.read().strip('\n')

def setStandby(id):
    cv.imwrite('data/stream_frames/{}/frame.jpg'.format(id), STANDBY_FRAME)

def addToWhiteList(ip):
    if not isWhitelisted(ip):
        with open('data/whitelist.txt', 'a') as list:
            list.write('{}\n'.format(ip))

def addToBlackList(ip):
    if not isBlacklisted(ip):
        with open('data/blacklist.txt', 'a') as list:
            list.write('{}\n'.format(ip))

def isWhitelisted(ip):
    with open('data/whitelist.txt', 'r') as list:
        if list.readline().strip('\n') == ip:
            return True # This IP is whitelisted

    return False # IP was not found in whitelist

def isBlacklisted(ip):
    with open('data/blacklist.txt', 'r') as list:
        if list.readline().strip('\n') == ip:
            return True # This IP is blacklisted

    return False # IP was not found in blacklist
