FROM ubuntu:20.04
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    docker.io \
    && rm -rf /var/lib/apt/lists/*

ADD requirements.txt /requirements.txt
RUN pip install -r /requirements.txt

RUN mkdir -p /opt/app/

WORKDIR /opt/app/
COPY . /opt/app/

ENV LOG_LEVEL=20
ENV PREFETCH_VALUE=1
ENV API_URL=http://api:7000/
ENV UNFINISHED_JOB_QUEUE=unfinished_job_queue
ENV FINISHED_JOB_QUEUE=finished_job_queue

ENV PRIVATE_TASKS=/tasks/
ENV PRIVATE_TASKS_BY_UID=/tasks/uid/
ENV PRIVATE_MODELS_BY_ID=/models/id/
ENV PRIVATE_MODELS_BY_HUMAN_READABLE_ID=/models/human_readable_id/
ENV PRIVATE_MODEL_ZIPS_BY_ID=/models/zip/uid/
ENV PRIVATE_OUTPUT_ZIPS_BY_UID=/outputs/uid/
ENV PRIVATE_INPUT_ZIPS_BY_ID=/inputs/id/
ENV GPU_UUID=""
ENV NETWORK_NAME=inference_server_private
ENV VOLUME_SENDER_DOCKER_TAG=mathiser/inference_server:volume_sender
ENV BUSYBOX_DOCKER_TAG=busybox:1.35

CMD python3 /opt/app/main.py