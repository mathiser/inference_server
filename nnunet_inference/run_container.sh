#!/bin/sh
docker run -it --rm --gpus=all --ipc=host -p 8000:8000 --network="host" -v Task5003_WholeHeart_CT:/opt/app/models mathiser/inference_server:nnunet_inference
