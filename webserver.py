from flask import Flask, render_template, Response, request
from multiprocessing import Process as process
from waitress import serve
import cv2 as cv
from systemhelper import getClientCount, toggleStatus, getStatus, lock, unlock, readLock
import datetime, time, os

HOST = '0.0.0.0'
PORT = 8000
app = Flask(__name__)
PROCESSES = []
app.config['CACHE_TYPE'] = 'null' # TODO: delete

@app.route('/', methods=['GET', 'POST'])
def index():
    '''index (default) route'''
    # Handle posts
    if request.method == 'POST':
        # TODO: send an alert notifying that alerts have been turned on/off
        render_template('index.html', clients=getClientCount(), status=toggleStatus())

    # Return page template
    return render_template('index.html', clients=getClientCount(), status=getStatus())

@app.route('/video_thumbnail/<id>')
def video_thumbnail(id):
    return Response(getClientStream(id, True), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/video_feed/<id>')
def video_feed(id):
    return Response(getClientStream(id), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/video_recordings')
def video_recordings():
    path = 'static/recordings'
    return render_template('recordings.html', list=list_files(path))

@app.route('/watch_stream/<id>')
def watch_stream(id):
    return render_template('watch_stream.html', id=id)

@app.route('/watch_video/<path:video>')
def watch_video(video):
    return render_template('watch_video.html', video=video)

def list_files(path):
    '''List the contents of the given directory'''
    # Extremely helpful resource: https://stackoverflow.com/a/10961991
    list = dict(name=os.path.basename(path), children=[], size=0)
    try: lst = os.listdir(path)
    except OSError:
        pass #ignore errors
    else:
        for name in lst:
            fn = os.path.join(path, name)
            if os.path.isdir(fn):
                list['children'].append(list_files(fn))
            else:
                list['children'].append(dict(name=fn))
            list['size'] += 1
    return list

def getClientStream(id, thumbnail_only=False):
    '''Get a client stream given their id. Yield a single frame if only a thumbnail_only is needed'''
    while True:
        if readLock(id) == 'unlocked':
            lock(id)

            filename = 'data/stream_frames/{}/frame.jpg'.format(id)
            img = cv.imread(filename, cv.IMREAD_UNCHANGED)
            unlock(id) # Done reading image. Unlock

            #possibly unnecessary encoding # TODO: see if this is necessary. might be able to just use cv.imread
            try:
                ret, buffer = cv.imencode('.jpg', img)
            except Exception as e:
                print(e)

            if ret:
                message = buffer.tobytes()

            yield(b'--frame\r\n'
                        b'Content-Type: image/jpeg\r\n\r\n' + message + b'\r\n')

            if thumbnail_only:
                return

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
