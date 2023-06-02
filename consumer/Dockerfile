FROM ubuntu:20.04
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    docker.io \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /home/app/
WORKDIR /home/app/
COPY . /home/app/

ADD requirements.txt requirements.txt
RUN pip install -r requirements.txt

ENV TZ=Europe/Copenhagen
ENV NETWORK_NAME=inference_server_backend
ENV API_HOSTNAME=private_api
ENV API_PORT=7000
ENV API_URL=http://private_api:7000
ENV LOG_LEVEL=20
ENV RABBIT_HOSTNAME=rabbit
ENV RABBIT_PORT=5672

ENV UNFINISHED_JOB_QUEUE=unfinished_job_queue
ENV FINISHED_JOB_QUEUE=finished_job_queue

ENV API_TASKS=/api/tasks/
ENV API_OUTPUT_ZIPS=/api/tasks/outputs/
ENV API_INPUT_ZIPS=/api/tasks/inputs/

ENV API_MODELS=/api/models/
ENV API_MODELS_BY_HUMAN_READABLE_ID=/api/models/human_readable_id/
ENV API_MODEL_ZIPS=/api/models/zips/
ENV GPU_UUID="-1"
ENV PREFETCH_VALUE=1

ENV BUSYBOX_DOCKER_TAG=busybox:1.35
ENV PYTHONUNBUFFERED=1
CMD python3 main.py
