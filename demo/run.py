import io
from PIL import Image
from kafka import KafkaConsumer, KafkaProducer
from grpc_test.torchserve_grpc_client import get_inference_stub, infer_image
import numpy as np
import configparser
import argparse

config = configparser.ConfigParser()
config.read("settings.cfg")

parser = argparse.ArgumentParser(description="Give information")
parser.add_argument("--room", help="room index for monitoring")
parser.add_argument("--model", default="STCNet_8f_CesleaFDD6", help="which model to use")
args = parser.parse_args()

### below 2 variables will be given for each container
ROOM_NUMBER = args.room
MODEL_NAME = args.model

BROKER = config["DEFAULT"]["BROKER"]
TORCH_SERVER = config["DEFAULT"]["TORCH_SERVER"]


def main():
    consumer = KafkaConsumer(bootstrap_servers=BROKER)
    consumer.subscribe(pattern=f"room_{ROOM_NUMBER}.*.color$")

    producer = KafkaProducer(bootstrap_servers=BROKER)

    ix = 0
    for msg in consumer:
        image = Image.open(io.BytesIO(msg.value))
        image = np.array(image)
        prediction = infer_image(get_inference_stub(target=TORCH_SERVER),
                                MODEL_NAME, image, ix)

        new_topic = msg.topic + ".prediction"
        if prediction != "0":
            producer.send(new_topic, bytes(str(prediction), 'utf-8'))
        
        print("Topic : ", msg.topic, prediction)

        ix += 1


if __name__ == "__main__":
    main()