import io
from PIL import Image, ImageDraw
import numpy as np
import cv2
from flask import Flask, Response, render_template
from kafka import KafkaConsumer
import ast

# Fire up the Kafka Consumer
ROOM_NUMBER = "1"
CAMERA_NUMBER = "3"
BROKER = '155.230.150.43:9092'

consumer1 = KafkaConsumer(bootstrap_servers=BROKER)
consumer1.subscribe(pattern=f"room_{ROOM_NUMBER}.realsense_{CAMERA_NUMBER}.*.color$")

consumer2 = KafkaConsumer(bootstrap_servers=BROKER)
consumer2.subscribe(pattern=f"room_{ROOM_NUMBER}.realsense_{CAMERA_NUMBER}.*.prediction$")

# Set the consumer in a Flask App
app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video', methods=['GET'])
def video():
    """
    This is the heart of our video display. Notice we set the mimetype to 
    multipart/x-mixed-replace. This tells Flask to replace any old images with 
    new values streaming through the pipeline.
    """
    return Response(
        get_video_stream(), 
        mimetype='multipart/x-mixed-replace; boundary=frame')

def get_video_stream():
    """
    Here is where we recieve streamed images from the Kafka Server and convert 
    them to a Flask-readable format.
    """
    for msg1, msg2 in zip(consumer1, consumer2):
        
        dict_str = msg2.value.decode("UTF-8")
        y_pred = ast.literal_eval(dict_str)
        
        top3 = list(y_pred.items())[:3]

        top3_str = ""
        for i in range(3):
            top3_str += "{}: {:.3f}\n".format(*top3[i])

        image = Image.open(io.BytesIO(msg1.value))
        image = np.array(image)

        h, w = image.shape[:-1]

        result_frame = np.zeros((h+80, w, 3), dtype=np.uint8)
        result_frame[:h, :w, :] = image

        # draw result on this frame
        y0, dy = h+20, 25
        for i, line in enumerate(top3_str.split('\n')):
            y = y0 + i*dy
            cv2.putText(result_frame, line, (10, y ), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,255,0), 1)

        # result_frame = cv2.putText(result_frame, top3_str, (10,h+65), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 1)

        result_img = Image.fromarray(result_frame)
        img_byte_arr = io.BytesIO()
        result_img.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()

        # draw action labels on image
        yield (b'--frame\r\n'
            b'Content-Type: image/jpg\r\n\r\n' + img_byte_arr + b'\r\n\r\n')
                
if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)