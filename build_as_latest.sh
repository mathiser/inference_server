#!/bin/bash
docker build ./job_consumer/ -t mathiser/inference_server:job_consumer_latest
docker build ./private_api/ -t mathiser/inference_server:private_api_latest
docker build ./public_api/ -t mathiser/inference_server:public_api_latest

docker push mathiser/inference_server:job_consumer_latest
docker push mathiser/inference_server:private_api_latest
docker push mathiser/inference_server:public_api_latest
