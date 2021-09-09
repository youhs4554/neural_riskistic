torchserve --stop && \
torchserve --start --ncs --model-store model_store --models STCNet_8f_CesleaFDD6.mar --ts-config config.properties  # if additional model is developed, append othre .mar files