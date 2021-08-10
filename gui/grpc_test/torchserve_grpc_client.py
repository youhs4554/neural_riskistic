import grpc
from . import inference_pb2
from . import inference_pb2_grpc
from . import management_pb2
from . import management_pb2_grpc
import sys
import cv2
from PIL import Image
import io


def int_to_bytes(number):
    return number.to_bytes(length=(8 + (number + (number < 0)).bit_length()) // 8, byteorder='big', signed=True)


def get_inference_stub():
    channel = grpc.insecure_channel('155.230.150.42:7070')
    stub = inference_pb2_grpc.InferenceAPIsServiceStub(channel)
    return stub


def get_management_stub():
    channel = grpc.insecure_channel('155.230.150.42:7071')
    stub = management_pb2_grpc.ManagementAPIsServiceStub(channel)
    return stub


def infer(stub, model_name, input_data):
    response = stub.Predictions(
        inference_pb2.PredictionsRequest(model_name=model_name, input=input_data))
    try:
        prediction = response.prediction.decode('utf-8')
    except grpc.RpcError as e:
        exit(1)

    return prediction


def imarr2bytes(image):
    image_pil = Image.fromarray(image).convert("RGB")
    with io.BytesIO() as byte_io:
        image_pil.save(byte_io, format="jpeg")
        image_buffer = byte_io.getvalue()
    return image_buffer


def infer_image(stub, model_name, image, ix):
    # np->bytes
    image_buffer = imarr2bytes(image)
    input_data = {'data': image_buffer,
                  "frame_count": int_to_bytes(ix)
                  }

    # actual inference
    res = infer(stub, model_name, input_data)
    return res


def infer_camera(stub, model_name, cam_id=None):
    if cam_id is None:
        cam_id = 0  # default camera

    camera = cv2.VideoCapture(cam_id)
    camera_on = camera.isOpened()

    ix = 0

    while camera_on:
        ret, image = camera.read()
        prediction = infer_image(stub, model_name, image, ix)
        print(prediction)

        ix += 1

    camera.release()


def register(stub, model_name):
    params = {
        'url': "https://torchserve.s3.amazonaws.com/mar_files/{}.mar".format(model_name),
        'initial_workers': 1,
        'synchronous': True,
        'model_name': model_name
    }
    try:
        response = stub.RegisterModel(
            management_pb2.RegisterModelRequest(**params))
        print(f"Model {model_name} registered successfully")
    except grpc.RpcError as e:
        print(f"Failed to register model {model_name}.")
        print(str(e.details()))
        exit(1)


def unregister(stub, model_name):
    try:
        response = stub.UnregisterModel(
            management_pb2.UnregisterModelRequest(model_name=model_name))
        print(f"Model {model_name} unregistered successfully")
    except grpc.RpcError as e:
        print(f"Failed to unregister model {model_name}.")
        print(str(e.details()))
        exit(1)


if __name__ == '__main__':
    # args:
    # 1-> api name [infer, register, unregister]
    # 2-> model name
    # 3-> model input for prediction
    args = sys.argv[1:]
    if args[0] == "infer":
        #infer(get_inference_stub(), args[1], args[2])
        infer_camera(get_inference_stub(), args[1], cam_id=0)
    else:
        api = globals()[args[0]]
        api(get_management_stub(), args[1])
