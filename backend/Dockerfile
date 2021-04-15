# "docker login nvcr.io" command is required to use base image
# API key from NGC(Nvidia GPU Cloud) : https://ngc.nvidia.com/setup/api-key
FROM nvcr.io/nvidia/l4t-pytorch:r32.5.0-pth1.7-py3



# build image
# docker build -t {image_name} .

# create container & run
# docker run --name {container_name} -v $(pwd):/path/to/storage -p {service_port}:{service_port} {image_name}

# create container & run (realsense example)
# docker run -it --rm --runtime nvidia --network host --device /dev/video0:/dev/video0 --device /dev/video1:/dev/video1 --device /dev/video2:/dev/video2 nvcr.io/nvidia/l4t-pytorch:r32.5.0-pth1.7-py3
