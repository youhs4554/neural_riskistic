import sys
from handler_utils import int_from_bytes, rotate
import torch
import torchvision.transforms as transforms
import io
import base64
from PIL import Image
import os
from ts.torch_handler.base_handler import BaseHandler
import zipfile

class ActivityClassifier(BaseHandler):
    """
    A custom model handler implementation.
    """

    def __init__(self):
        self._context = None
        self.initialized = False
        self.explain = False
        self.target = 0
        self.cache = {}

    def initialize(self, context):
        """
        Initialize model. This will be called during model loading time
        :param context: Initial context contains model server system properties.
        :return:
        """
        properties = context.system_properties
        self.map_location = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = torch.device(
            self.map_location + ":" + str(properties.get("gpu_id"))
            if torch.cuda.is_available()
            else self.map_location
        )
        self.manifest = context.manifest

        model_dir = properties.get("model_dir")
        model_pt_path = None
        if "serializedFile" in self.manifest["model"]:
            serialized_file = self.manifest["model"]["serializedFile"]
            model_pt_path = os.path.join(model_dir, serialized_file)
            hparams_file = os.path.join(model_dir, "hparams.yaml")  # this file shoud be given at --extra-files option

        # # model def file
        # model_file = self.manifest["model"].get("modelFile", "")

        # #  load the model, refer 'custom handler class' above for details
        # ckpt_dir = "../model_ckpt/STCNet_8f_CesleaFDD6-1/version_2"
        # ckpt = os.path.join(ckpt_dir, "checkpoints/epoch=45.ckpt")
        # hparams_file = os.path.join(ckpt_dir, "hparams.yaml")

        # extract input clip length from modelName(=STCNet_8f_CesleaFDD6) : 8f -> 8
        # print("######################## FOOOOOOOOOF : ", self.manifest)
        self.L = int(self.manifest["model"]["modelName"].split("_")[-2][:-1])

        with zipfile.ZipFile(model_dir + '/activity_lib.zip', 'r') as zip_ref:
            zip_ref.extractall(model_dir)

        sys.path.append("./activity_lib")
        sys.path.append("./activity_lib/models")
        print("##############################", os.listdir("./activity_lib"))

        from activity_lib.models.video_classifier import LightningVideoClassifier

        # load ckpt through pytorch_lightning
        pl_model = LightningVideoClassifier.load_from_checkpoint(model_pt_path,
                                                                   hparams_file=hparams_file,
                                                                   hparam_overrides={"batch_per_gpu": 1})

        pl_model.to(self.device)
        pl_model.eval()

        # detach model instanche for evaluation
        self.model = pl_model.model
        
    def preprocess(self, data):
        """
        Transform raw input into model input data.
        :param batch: list of raw requests, should match batch size
        :return: list of preprocessed model input data
        """
        # data : list of requests
        image = data[0].get("data")
        frame_count = int_from_bytes(data[0].get("frame_count"))
        L = self.L # input clip legnth

        # Take the input data and make it inference ready
        image_processing = transforms.Compose([
            transforms.Resize((128,171)),
            transforms.CenterCrop(112),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                std=[0.229, 0.224, 0.225])
        ])
        
        if isinstance(image, str):
            # if the image is a string of bytesarray.
            image = base64.b64decode(image)

        # If the image is sent as bytesarray
        if isinstance(image, (bytearray, bytes)):
            image = Image.open(io.BytesIO(image))
            image = image_processing(image)
        else:
            # if the image is a list
            image = torch.FloatTensor(image)    

        data_preprocess = None
        
        # invoke flag. It is true when the minimum input length condition is satisfied
        invoke_flag = frame_count >= L 
        self.invoke_flag = invoke_flag

        if not invoke_flag:
            # if cache is not full yet -> add latest image to the cache
            key = frame_count % L
            self.cache[key] = image
        else:
            # if cache is full -> rotate and replace old frame with latest image
            self.cache = rotate(self.cache, n=-1) # rote dict first
            self.cache[L-1] = image # replace oldest image with latest image
            data_preprocess = torch.stack(list(self.cache.values())).transpose(0,1)
            data_preprocess = data_preprocess[None, ...]  # expand batch_dim

        print("####################### invoke_flag : ", self.invoke_flag)
        print("####################### length of cahed data : ", len(self.cache))
        if data_preprocess is not None:
            print("####################### shape of processed data : ", data_preprocess.shape)
        
        return data_preprocess

    def inference(self, data):
        """
        The Inference Function is used to make a prediction call on the given input request.
        The user needs to override the inference function to customize it.
        Args:
            data (Torch Tensor): A Torch Tensor is passed to make the Inference Request.
            The shape should match the model input shape.
        Returns:
            Torch Tensor : The Predicted Torch Tensor is returned in this function.
        """
        if not self.invoke_flag:
            return 

        marshalled_data = data.to(self.device)

        n, _, d, h, w = marshalled_data.shape

        # dummy mask inputs since model code assume target masks coming with input but they are never used.
        dummy_masks = torch.ones(n,1,d,h,w).to(self.device)

        with torch.no_grad():
            clip_out, _ = self.model(marshalled_data, dummy_masks)
            results = torch.softmax(clip_out, 1)

        return results

    def postprocess(self, inference_output):
        """
        Return inference result.
        :param inference_output: list of inference output
        :return: list of predict results
        """
        if inference_output is None:
            return [0]

        print("####################### shape of inference data : ", type(inference_output), inference_output.shape)

        # Take output from network and post-process to desired format
        __classes = dict(enumerate(['background', 
                 'falling', 
                 'sitting', 
                 'sleeping', 
                 'standing',
                 'walking']))
        probs, predictions = inference_output.sort(1, True)
        probs = probs.tolist()
        predictions = predictions.tolist()

        # resulting response
        res = [ 
            {
                __classes[pred]: prob for pred,prob in zip(pred_sample, prob_sample)
            } for pred_sample, prob_sample in zip(predictions, probs)
        ]
        return res
