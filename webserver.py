from flask import Flask, render_template, Response, request
import cv2 as cv
import functions as helper
import time

app = Flask(__name__)
app.config["CACHE_TYPE"] = "null" # TODO: delete

@app.route('/', methods=['GET', 'POST'])
def index():
    '''index (default) route'''
    # Handle posts (alarm toggles)
    if request.method == 'POST':
        render_template('index.html', clients=helper.getClientCount(), status=helper.toggleStatus())

    # Return page template
    return render_template('index.html', clients=helper.getClientCount(), status=helper.getStatus())

@app.route('/video_feed/<id>')
def video_feed(id):
    return Response(getClientStream(id), mimetype='multipart/x-mixed-replace; boundary=frame')

def getClientStream(id):
    '''Get a client stream given their id'''
    while True:
        with open('data/stream_frames/{}.txt'.format(id), 'r') as file:
            name = file.read()
        if name: # Only update when file is not empty  (not being written to)
            filename = 'data/stream_frames/{}{}.jpg'.format(id, name)
            #print('reading file:', filename) # TODO: delete

            with open(filename, 'rb') as f:
                img_complete = f.read()[-2:] == b'\xff\xd9' # True if jpeg if complete, false otherwise

            if img_complete:
                #print('file')
                img = cv.imread(filename, cv.IMREAD_UNCHANGED)
                #clone = img.copy()

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

if __name__ == '__main__':
    # TODO: disable DEBUG mode
    app.run(port=80, debug=True)
