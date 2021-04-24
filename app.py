from flask import Flask, render_template, Response
import cv2 as cv

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video-feed')
def video_feed():
    return Response(stream(), mimetype='multipart/x-mixed-replace; boundary=frame')


def stream():
    camera = cv.VideoCapture(0)

    if not camera.isOpened():
        #Attempt to open capture device once more, after a failure
        camera.open()
        if not camera.isOpened():
            print('Cannot open camera')
            exit()

    # Camera properties
    width = int(camera.get(3))
    height = int(camera.get(4))
    fps = camera.get(5)

    ret, frame1 = camera.read()
    ret, frame2 = camera.read()
    while camera.isOpened():
        motion, motionFrame = detectMotion(frame1, frame2)
        #cv.imshow('Video', frame1)

        #ret, buffer = cv.imencode('.jpg', frame1)
        ret, buffer = cv.imencode('.jpg', motionFrame)
        motionFrame = buffer.tobytes()
        yield (b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + motionFrame + b'\r\n')


        if motion:
            print('motion')



        frame1 = frame2
        ret, frame2 = camera.read()

        if cv.waitKey(1) == ord('q') or not ret:
            break

    camera.release()
    cv.destroyAllWindows()


def detectMotion(f1, f2):
    difference = cv.absdiff(f1, f2)
    gray_difference = cv.cvtColor(difference, cv.COLOR_BGR2GRAY)
    blur = cv.GaussianBlur(gray_difference, (5, 5), 0)
    __, thresh = cv.threshold(blur, 20, 255, cv.THRESH_BINARY)
    dilated = cv.dilate(thresh, None, iterations=3)
    contours, __ = cv.findContours(dilated, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)

    #cv.imshow('motion', blur)

    detected = False
    motionFrame = f1.copy()
    for contour in contours:
        # Source: Divyanshu Shekhar - https://divyanshushekhar.com/motion-detection-opencv/
        (x, y, w, h) = cv.boundingRect(contour)
        if cv.contourArea(contour) >= 7500:
            detected = True
            cv.rectangle(motionFrame, (x, y), (x+w, y+h), (255, 255, 255), 1)
            cv.putText(motionFrame, "Movement", (6, 28), cv.FONT_HERSHEY_SIMPLEX, 1.125, (0, 0, 224), 2)

    #cv.imshow('Motion Detector', motionFrame)


    return detected, motionFrame

if __name__ == '__main__':
    app.run(debug=True)
