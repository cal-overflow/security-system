import numpy
import cv2 as cv

def record():
    '''Record video from capture device. Save to output file.'''
    # Define capture device
    camera = cv.VideoCapture(0)

    if not camera.isOpened():
        # Attempt to open capture device (camera) one more time.
        camera.open()

        # Camera did not open on backup attempt, recording unavailable
        if not camera.isOpened():
            print('Cannot open camera')
            exit()

    # Set properties of camera (width, height, fps)
    WIDTH = int(camera.get(3))
    HEIGHT = int(camera.get(4))
    FPS = camera.get(5)
    print('Capture resolution: {}x{}\nFPS: {}'.format(WIDTH, HEIGHT, FPS))

    fourcc = cv.VideoWriter_fourcc(*'XVID')
    output = cv.VideoWriter('output.avi', fourcc, FPS, (WIDTH, HEIGHT), True)
    while True:
        # Capture the frame
        ret, frame = camera.read()
        if not ret:
            print('Issue receiving frame from camera.')
            break

        # Write frame to output file
        output.write(frame)
        # Display frame
        cv.imshow('Video', frame)

        if cv.waitKey(1) == ord('q'):
            break

    camera.release()
    output.release()
    cv.destroyAllWindows()

def play(file_name):
    vid = cv.VideoCapture(file_name)
    print('Playing video: \'{}\'. Video framerate: {}'.format(file_name, vid.get(5)))
    update_delay = int(1000.0 / vid.get(5)) # delay between frames
    print(update_delay)

    while vid.isOpened():
        ret, frame = vid.read()

        if not ret:
            print('Issue reading video file.')
            break

        cv.imshow('Video Display', frame)
        cv.waitKey(update_delay)
        if cv.waitKey(1) == ord('q'):
            break

    vid.release()
    cv.destroyAllWindows()

if __name__ == '__main__':
    choice = input('Enter:\n 1 - video capture\n 2 \'filename\' - video playback\n 3 - exit\nChoice: ')
    while int(choice[0]) != 3:
        if int(choice[0]) == 1:
            record()

        elif int(choice[0]) == 2:
            #play('output.avi')
            # TODO: change this back to what's below
            play(choice[2:])

        choice = input('Choice: ')
