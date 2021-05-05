import cv2 as cv
import smtplib
import datetime
import time

# Movement detection threshold
THRESHOLD = 10000

# data for each frame = {'img': image, 'motion': boolean, 'FPS': fps, 'WIDTH': width, 'HEIGHT': height}
def record(frames, already_recording, SECONDS, id):
    '''Record video when motion is detected. Includes the few seconds prior to motion detection and few seconds after the motion stops.'''
    FPS = frames[0]['FPS']
    WIDTH = frames[0]['WIDTH']
    HEIGHT = frames[0]['HEIGHT']
    motion = []

    for frame in frames:
        #print(frame)
        motion.append(frame['MOTION'])

    # Check if there has been motion in the last few seconds
    movement_lately = True in motion[len(motion) - (FPS * SECONDS * 2):]
    output_file = None

    if not movement_lately:
        #stop the recording. Write to a video file

        fourcc = cv.VideoWriter_fourcc(*'XVID')
        #TODO: need to change name of output file (probably to the date/time)
        output_file = 'data/recordings/{}CAM{}.avi'.format(datetime.datetime.now().strftime("%m-%d%Y-%H:%M:%S"), id)
        output = cv.VideoWriter(output_file, fourcc, FPS, (WIDTH, HEIGHT), True)

        for frame in frames:
            # Write each frame to the output file.
            output.write(drawRecording(frame['FRAME'], WIDTH, HEIGHT))
            cv.waitKey(1000 // FPS)

        output.release() # Completed writing to output file

    return movement_lately, output_file

def alert(id):
    '''Notify (via email) that motion has been detected.'''
    gmail_user = ''
    gmail_password = ''

    sent_from = gmail_user
    to = [] # Email recipients
    subject = 'ALERT - Security System'
    body = 'ALERT: Movement has been detected by the security system on {}'.format(datetime.datetime.now().strftime("%d/%m/%Y at %H:%M:%S"))

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

def getFPS():
    '''Get the true FPS (including processing) from the camera'''
    camera = cv.VideoCapture(0)

    start_time = time.time()
    count = 0
    while int(time.time() - start_time) < 1: # TODO: change back to 10
        ret, frame = camera.read()
        count += 1 # number of frames

    camera.release()
    return int(count / 10)

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
            cv.putText(frame, 'MOTION', (10, 16), cv.FONT_HERSHEY_PLAIN, 1, (0, 0, 224), 2, cv.FILLED, False)

    return detected, frame

def drawTime(frame, WIDTH, HEIGHT):
    '''Draw the date/time on the given frame.'''
    cv.putText(frame, datetime.datetime.now().strftime("%c"), (10, HEIGHT - 10), cv.FONT_HERSHEY_PLAIN, 1, (255, 255, 255), 2, cv.FILLED, False)
    return frame

def drawRecording(frame, WIDTH, HEIGHT):
    '''Draw a recording message on the given frame'''
    text = 'RECORDING' if (int(time.time()) % 2 == 0) else ''
    cv.putText(frame, text, (WIDTH - 140, 16), cv.FONT_HERSHEY_PLAIN, 1, (0, 0, 224), 2, cv.FILLED, False)
    return frame

def getClientCount():
    '''Return the current number of clients'''
    with open('data/clients.txt', 'r') as file:
        count = int(file.read())
    #print('Client count:', count) # TODO: delete
    return count

def updateClientCount(i):
    '''Update number of clients'''
    with open('data/clients.txt', 'w') as file:
        file.write(str(i))
    #print('Client count:', i) # TODO: delete

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

    with open('data/alarm_status.txt', 'w') as file:
        file.write(new)

    return new
