from flask import Flask, render_template, Response, request
from multiprocessing import Process as process
import cv2 as cv
import systemhelper as helper
import datetime, time

HOST = '0.0.0.0'
PORT = 8001
app = Flask(__name__)
PROCESSES = []
app.config["CACHE_TYPE"] = "null" # TODO: delete

@app.route('/', methods=['GET', 'POST'])
@app.route('/toggle_form', methods=['GET', 'POST'])
def index():
    '''index (default) route'''
    # Handle posts
    if request.method == 'POST':
        # TODO: send an alert notifying that alerts have been turned on/off
        render_template('index.html', clients=helper.getClientCount(), status=helper.toggleStatus())

    # Return page template
    return render_template('index.html', clients=helper.getClientCount(), status=helper.getStatus())

@app.route('/video_feed/<id>')
def video_feed(id):
    return Response(getClientStream(id), mimetype='multipart/x-mixed-replace; boundary=frame')

def getClientStream(id):
    '''Get a client stream given their id'''
    while True:
        if helper.readLock(id) == 'unlocked':
            helper.lock(id)

            filename = 'data/stream_frames/{}/frame.jpg'.format(id)

            # TODO: see if this does anything. I don't think this works as it should
            #with open(filename, 'rb') as f:
                #img_complete = f.read()[-2:] == b'\xff\xd9' # True if jpeg if complete, false otherwise

            #if img_complete:
                #print('file')
            img = cv.imread(filename, cv.IMREAD_UNCHANGED)
            helper.unlock(id) # Done reading image. Unlock

            #possibly unnecessary encoding # TODO: see if this is necessary. might be able to just use cv.imread
            # Not sure if this if statement helps at all. (Initially this helped with the imencode -> '!image empty error')
            # TODO: re-visit this error
            #if type(img) != None:
            try:
                ret, buffer = cv.imencode('.jpg', img)
            except Exception as e:
                print(e)

            if ret:
                message = buffer.tobytes()

            yield(b'--frame\r\n'
                        b'Content-Type: image/jpeg\r\n\r\n' + message + b'\r\n')
            time.sleep(.125)

if __name__ == '__main__':
    # TODO: disable DEBUG mode
    #while True:
    try:
        print('{} [INFO]: Starting webserver on port {}'.format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), PORT))
        app.run(host=HOST, port=PORT, debug=False)
    except Exception as e:
        print('{} [INFO]: Webserver crashed. Cause:\n{}'.format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), e))
        time.sleep(5)
        print('{} [INFO]: Restarting Webserver'.format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
