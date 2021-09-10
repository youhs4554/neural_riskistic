import io
import re
from utils import DetectionVisualization, bb_intersection_over_union
from PIL import Image
from kafka import KafkaConsumer, KafkaProducer
from grpc_test.torchserve_grpc_client import get_inference_stub, infer_image
import numpy as np
import cv2
import configparser
import requests
import os
import json
import argparse
import base64
from kafka import TopicPartition

config = configparser.ConfigParser()
config.read("settings.cfg")

parser = argparse.ArgumentParser(description="Give information")
parser.add_argument("--room", help="room index for monitoring")
parser.add_argument("--model", default="STCNet_8f_CesleaFDD6",
                    help="model architecture")
parser.add_argument("--show_only_person", dest="show_only_person", action="store_true",
                    help="show only person detection result if true")
parser.set_defaults(show_only_person=False)
args = parser.parse_args()

# below 3 variables will be given for each container
ROOM_NUMBER = args.room
MODEL_ARCH = args.model
SHOW_ONLY_PERSON = args.show_only_person

### kafka config ###
BROKER = config["KAFKA"]["BROKER"]

### activity recognition config ###
ACTION_MODEL_URL = config["ACTION"]["MODEL_URL"]
WORKER_PER_MODEL = config["ACTION"]["WORKER_PER_MODEL"]
ACTION_API = config["ACTION"]["API"]
WIDTH = int(config["ACTION"]["INPUT_WIDTH"])
HEIGHT = int(config["ACTION"]["INPUT_HEIGHT"])

### human detection config ###
DETECTION_API = config["DETECTION"]["API"]

### active-zone config ###
ALPHA = float(config["ACTIVE-ZONE"]["ALPHA"])  # transparency
# for toggling mode_in_bed
IOU_THRESH = float(config["ACTIVE-ZONE"]["IOU_THRESH"])
ZONE_WIDTH = int(config["ACTIVE-ZONE"]["WIDTH"])
ZONE_VERTICAL_OFFSET = int(config["ACTIVE-ZONE"]["VERTICAL_OFFSET"])


### etc config ###
# check box movement
BOX_MOVEMENT_TRESH = float(config["ETC"]["BOX_MOVEMENT_TRESH"])
TARGET_OBJ = config["ETC"]["TARGET_OBJ"]


consumer = KafkaConsumer(bootstrap_servers=BROKER)
all_topics = consumer.topics()

# for topic filtering
CAMERA_TOPIC_REGEX = f"room_{ROOM_NUMBER}.realsense_3.stream.color$"

regex = re.compile(CAMERA_TOPIC_REGEX)
available_camera_topics = filter(regex.match, all_topics)

for i, topic_name in enumerate(available_camera_topics):
    model_name = "model@" + topic_name
    print(f"[model-{i}] ===> Starting up model at {topic_name}...",
          end="", flush=True)
    # register action model
    requests.post(ACTION_MODEL_URL, headers={'Content-type': 'application/json'},
                  data=json.dumps({"model_name": model_name, "url": MODEL_ARCH+".mar"}))
    # start worker
    requests.put(os.path.join(ACTION_MODEL_URL, model_name),
                 data={"min_worker": "1"})
    print('\033[31m \033[43m', "done!", '\033[0m')


def main():
    consumer = KafkaConsumer(bootstrap_servers=BROKER)
    consumer.subscribe(pattern=f"room_{ROOM_NUMBER}.realsense_3.stream.color$")

    action_consumer = KafkaConsumer(bootstrap_servers=BROKER)
    producer = KafkaProducer(bootstrap_servers=BROKER)

    ix = 0

    # for detection result visualization
    dv = DetectionVisualization()

    for msg in consumer:

        with io.BytesIO(msg.value) as stream:
            image = Image.open(stream).convert("RGB")
            image = np.array(image)

        # dimension of original frame
        raw_height, raw_width = image.shape[:-1]
        mode_in_bed = False

        detection_topic = msg.topic + ".detection"
        detection_box_topic = msg.topic + ".detection.box"
        action_topic = msg.topic + ".action"

        # # TODO. move offset to find fall history
        # tp = TopicPartition(action_topic, 0)
        # action_consumer.assign([tp])
        # start = 6305
        # end = start + 10
        # action_consumer.seek(tp, start)
        # for action_msg in action_consumer:
        #     if action_msg.offset > end:
        #         break
        #     else:
        #         print(action_msg)

        # request YOLO results
        post_data = {"image": base64.b64encode(msg.value).decode("utf-8"),
                     "get_img_flg": False}
        res = requests.post(DETECTION_API,
                            json=post_data).json()
        person_box = list(
            filter(lambda x: x.get("obj_name") == TARGET_OBJ, res["resultlist"]))
        for i in range(len(person_box)):
            # to handle multi-person
            person_box[i]["obj_name"] = "{}-{}".format(TARGET_OBJ, i+1)

        if SHOW_ONLY_PERSON:
            detection_image = dv.draw_detections(
                image, person_box)
        else:
            detection_image = dv.draw_detections(
                image, res["resultlist"])

        activezone_frame = np.zeros_like(image)

        # draw active zone near bed
        zone_size = (ZONE_WIDTH, int(ZONE_WIDTH*0.85))
        zone_x, zone_y = (raw_width // 2 - zone_size[0] // 2,
                          raw_height // 2 - zone_size[1] // 2 + ZONE_VERTICAL_OFFSET)
        activezone_frame = cv2.rectangle(activezone_frame, (zone_x, zone_y), (int(zone_x+zone_size[0])+1,
                                                                              int(zone_y+zone_size[1])+1), (255, 255, 128), -1)

        # apply overlay
        cv2.addWeighted(activezone_frame, ALPHA, image, 1 - ALPHA,
                        0, detection_image)

        if len(person_box) == 0:
            print(f"no person is detected at {msg.topic}")
            background_prediction = {"background": 100.0, "walking": 0.0,
                                     "standing": 0.0, "sitting": 0.0, "falling": 0.0, "sleeping": 0.0}
            background_prediction = json.dumps(background_prediction)

            cv2.putText(detection_image, "Status : room is empty", (5, 15),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1, cv2.LINE_AA)

            # update detection_topic
            producer.send(detection_topic, cv2.imencode(
                ".jpg", cv2.cvtColor(detection_image, cv2.COLOR_BGR2RGB))[1].tobytes())

            # update action_topic
            producer.send(action_topic, bytes(
                str(background_prediction), 'utf-8'))

            continue

        first_person_box = person_box[0]["bounding_box"]

        # (x_min,y_min,w,h) => (x_min,y_min,x_max,y_max)
        first_person_box = (
            first_person_box["x_min"],
            first_person_box["y_min"],
            first_person_box["x_min"]+first_person_box["width"],
            first_person_box["y_min"]+first_person_box["height"],
        )

        active_zone_box = (
            zone_x,
            zone_y,
            zone_x+zone_size[0],
            zone_y+zone_size[1],
        )

        iou = bb_intersection_over_union(first_person_box, active_zone_box)
        if iou > IOU_THRESH:
            mode_in_bed = True
            print("####### person is in bed ###########")
        else:
            mode_in_bed = False

        # update detection_topic
        producer.send(detection_topic, cv2.imencode(
            ".jpg", cv2.cvtColor(detection_image, cv2.COLOR_BGR2RGB))[1].tobytes())

        image = Image.open(io.BytesIO(msg.value))
        image = np.array(image)
        image = cv2.resize(image, (WIDTH, HEIGHT))
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        prediction = infer_image(get_inference_stub(target=ACTION_API),
                                 "model@" + msg.topic, image, ix)
        if prediction != "0":
            prediction = json.loads(prediction)
            prediction_list = list(prediction)

            if mode_in_bed and prediction_list[0] != "sleeping":
                # fallback prediction of mode_in_bed
                y_pred = "on_bed"
                prediction = {"on_bed": 1.0, "walking": 0.0,
                              "standing": 0.0, "sitting": 0.0, "falling": 0.0, "sleeping": 0.0}
            else:
                # top-1
                y_pred = prediction_list[0]

            cv2.putText(detection_image, "Status : {}".format(y_pred), (5, 15),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1, cv2.LINE_AA)

            for key in prediction.keys():
                prediction[key] *= 100
            prediction = json.dumps(prediction)

            # update action_topic
            producer.send(action_topic, bytes(str(prediction), 'utf-8'))

        print("Topic : ", msg.topic, prediction)

        # update detection_box_topic
        producer.send(detection_box_topic, bytes(
            str(person_box), 'utf-8'
        ))

        # update detection_topic
        producer.send(detection_topic, cv2.imencode(
            ".jpg", cv2.cvtColor(detection_image, cv2.COLOR_BGR2RGB))[1].tobytes())

        ix += 1


if __name__ == "__main__":
    main()
