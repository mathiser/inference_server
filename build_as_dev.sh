#!/bin/bash

docker build ./consumer/ -t mathiser/inference_server:consumer_dev
docker build ./controller/ -t mathiser/inference_server:controller_dev


docker push mathiser/inference_server:controller_dev
docker push mathiser/inference_server:consumer_dev
