from flask import Flask, render_template, Response
import cv2 as cv
import time

app = Flask(__name__)
#manager = Manager(app)
app.config["CACHE_TYPE"] = "null" # TODO: delete

@app.route('/')
def index():
    return render_template('index.html', clients=getClients())

@app.route('/video_feed/<id>')
def video_feed(id):
    return Response(getClientStream(id), mimetype='multipart/x-mixed-replace; boundary=frame')

def getClients():
    with open('clients.txt', 'r') as file:
        count = int(file.read()) # number of clients/cameras
    return count

def getClientStream(id):
    '''Get a client stream given their id'''
    while True:
        # 9 millisecond intervals where ms 6-9 are for reading. # TODO: fix this. This is the lazy way of fixing this.
        if not (6 <= int(time.time() * 1000) % 10 <= 8):
            continue

        filename = 'stream_frames//{}.jpg'.format(id)
        with open(filename, 'rb') as f:
            img_complete = f.read()[-2:] == b'\xff\xd9' # True if jpeg if complete, false otherwise

        if img_complete:
            #print('file')
            img = cv.imread(filename, cv.IMREAD_UNCHANGED)
            #clone = img.copy()

            #possibly unnecessary encoding # TODO: see if this is necessary. might be able to just use cv.imread
            # Not sure if this if statement helps at all. (Initially this helped with the imencode -> '!image empty error')
            # TODO: re-visit this error
            if type(img) != None:
                ret, buffer = cv.imencode('.jpg', img)
                if ret:
                    message = buffer.tobytes()

                    yield(b'--frame\r\n'
                            b'Content-Type: image/jpeg\r\n\r\n' + message + b'\r\n')

if __name__ == '__main__':
    # TODO: disable DEBUG mode
    app.run(debug=True)
