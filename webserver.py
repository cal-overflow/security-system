from flask import Flask, render_template, Response, request
from multiprocessing import Process as process
from waitress import serve
import cv2 as cv
import systemhelper as helper
import datetime, time

HOST = '0.0.0.0'
PORT = 8000
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
            img = cv.imread(filename, cv.IMREAD_UNCHANGED)
            helper.unlock(id) # Done reading image. Unlock

            #possibly unnecessary encoding # TODO: see if this is necessary. might be able to just use cv.imread
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
    #while True:
    #try:
    print('{} [WEB]: Starting webserver on port {}'.format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), PORT))
    serve(app, host=HOST, port=PORT)
    #except Exception as e:
        #print('{} [WEB]: Webserver crashed. Cause:\n{}'.format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), e))
        #time.sleep(5)
        #print('{} [WEB]: Restarting Webserver'.format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
