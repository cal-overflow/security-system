# Helpful functions and constants used by webserver, server, and client scripts
import cv2 as cv
import smtplib
import struct
from pathlib import Path
import datetime, time, math

###############################################
# CONSTANTS
PACKAGE_SIZE = struct.calcsize("P")

###############################################
# HELPER FUNCTIONS
###############################################

def timestamp():
    '''Returns the current date and time in the preferred format'''
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

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
    '''Unlock the lock corresponding to the given client id'''
    with open('data/stream_frames/{}/lock.txt'.format(id), 'w+') as file:
        file.write('unlocked')

def lock(id):
    '''Lock the lock corresponding to the given client id'''
    with open('data/stream_frames/{}/lock.txt'.format(id), 'w+') as file:
        file.write('locked')

def readLock(id):
    '''Returns "locked" if the lock corresponding to the given client id is locked. Otherwise returns "unlocked"'''
    with open('data/stream_frames/{}/lock.txt'.format(id), 'r') as file:
        return file.read().strip('\n')

def setStandby(id):
    '''Set the given client frame to the standby image'''
    cv.imwrite('data/stream_frames/{}/frame.jpg'.format(id), cv.imread('static/standby.jpg', cv.IMREAD_UNCHANGED))

def addToWhiteList(ip):
    '''Whitelist the given ip address'''
    if not isWhitelisted(ip):
        with open('data/whitelist.txt', 'a') as list:
            list.write('{}\n'.format(ip))

def addToBlackList(ip):
    '''Blacklist the given ip address'''
    if not isBlacklisted(ip):
        with open('data/blacklist.txt', 'a') as list:
            list.write('{}\n'.format(ip))

def isWhitelisted(ip):
    '''Return true if the given ip address is Whitelisted. Otherwise returns false'''
    with open('data/whitelist.txt', 'r') as list:
        if list.readline().strip('\n') == ip:
            return True # This IP is whitelisted

    return False # IP was not found in whitelist

def isBlacklisted(ip):
    '''Return true if the given ip address is Blacklisted. Otherwise returns false'''
    with open('data/blacklist.txt', 'r') as list:
        if list.readline().strip('\n') == ip:
            return True # This IP is blacklisted

    return False # IP was not found in blacklist
