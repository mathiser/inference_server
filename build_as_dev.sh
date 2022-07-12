#!/bin/bash

docker build ./job_consumer/ -t mathiser/inference_server:job_consumer_dev
docker build ./private_api/ -t mathiser/inference_server:private_api_dev
docker build ./public_api/ -t mathiser/inference_server:public_api_dev

docker push mathiser/inference_server:job_consumer_dev
docker push mathiser/inference_server:private_api_dev
docker push mathiser/inference_server:public_api_dev
