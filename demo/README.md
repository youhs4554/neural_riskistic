# Real-time activity monitoring demo

## Introduction
---
This demo is for video understanding in a hospital room. It communicate with RESTful PyTorch server. 

Multiple cameras installed in a room can independently monitor human behaviors in real-time (~68 FPS).

## Local demo with GUI (only for Windows)
---
You can download `.exe` file for local live demo. Please refer to our *[release page](https://github.com/youhs4554/neural_riskistic/releases)*.

<div align="left">
  <img src="local_demo.gif" width="450px" padding="10px"/><br>
</div>


## Build and run camera-monitor daemon service with Docker
This docker service permanently receives video frames in a room and records human activity status in corresponding topic in a Kafka cluster (for example, `room_1.realsense_3.stream.color.prediction`).
- Usage : `VERSION=<version> ROOM_NUMBER=<room_number> MODEL_NAME=<model_name> docker-compose up --build -d`
    > Note : <model_name> must be pre-registered in PyTorch server. TorchServe provide interface to register/manage custom models. Please refer to 
    [official TorchServe repository](https://github.com/pytorch/serve).
- Settings : `settings.cfg` file should be written as
    ```
    [DEFAULT]
    BROKER = <kafka_broker_ip:port>
    TORCH_SERVER = <torch_server_ip:port>
    ```