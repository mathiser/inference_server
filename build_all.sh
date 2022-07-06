#!/bin/bash
if [ "$#" -ne 1 ]; then
    echo "Arg must be a version string - e.g.: 1.2.3"
    exit 1
fi

docker build ./job_consumer/Dockerfile -t mathiser/inference_server:job_consumer_v$1
docker build ./private_api/Dockerfile -t mathiser/inference_server:private_api_v$1
docker build ./public_api/Dockerfile -t mathiser/inference_server:public_api_v$1
docker build ./volume_sender/Dockerfile -t mathiser/inference_server:volume_sender_v$1

docker push mathiser/inference_server:job_consumer_v$1
docker push mathiser/inference_server:private_api_v$1
docker push mathiser/inference_server:public_api_v$1
docker push mathiser/inference_server:volume_sender_v$1