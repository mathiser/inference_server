#!/bin/bash

docker build ./consumer/ -t mathiser/inference_server_consumer:latest
docker build ./controller/ -t mathiser/inference_server_controller:latest


docker push mathiser/inference_server_controller:latest
docker push mathiser/inference_server_consumer:latest
