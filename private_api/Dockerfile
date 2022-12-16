FROM python:3.9-buster

ADD requirements.txt /requirements.txt
RUN pip install -r /requirements.txt

RUN mkdir -p /home/app/
COPY . /home/app/
WORKDIR /home/app/
ENV TZ=Europe/Copenhagen
ENV RABBIT_DOCKER_TAG=rabbitmq:3.9.17
ENV PREFETCH_VALUE=1

ENV API_HOSTNAME=private_api
ENV API_PORT=7000
ENV API_URL=http://private_api:7000

ENV LOG_LEVEL=10

ENV DATA_DIR=/home/app/data
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

EXPOSE $API_PORT

CMD python3 main.py
