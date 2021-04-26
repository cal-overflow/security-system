
import numpy as np
import cv2
import time

# Define the duration (in seconds) of the video capture here
capture_duration = 10

cap = cv2.VideoCapture(0)

# Define the codec and create VideoWriter object
fourcc = cv2.VideoWriter_fourcc(*'XVID')
out = cv2.VideoWriter('output3.avi',fourcc, 20.0, (640,480))

start_time = time.time()
frameCount = 0
print('supposed fps:',cap.get(5))
while int(time.time() - start_time) < capture_duration:
    # wait for camera to grab next
    ret, frame = cap.read()
    # count number of frames
    frameCount = frameCount+1

print('Total frames: ',frameCount)


# Release everything if job is finished
cap.release()
out.release()
cv2.destroyAllWindows()
