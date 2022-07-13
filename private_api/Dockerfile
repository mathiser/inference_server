FROM python:3.9-buster

RUN apt-get update
ADD requirements.txt /requirements.txt
RUN pip install -r /requirements.txt

RUN mkdir -p /opt/app/ /opt/app/data/
COPY . /opt/app/
WORKDIR /opt/app/

ENV API_HOSTNAME=api
ENV API_PORT=7000
ENV API_URL=http://api:7000
ENV LOG_LEVEL=20
ENV DATA_DIR=/data
ENV RABBIT_HOSTNAME=rabbit
ENV RABBIT_PORT=5672
ENV UNFINISHED_JOB_QUEUE=unfinished_job_queue
ENV FINISHED_JOB_QUEUE=finished_job_queue

ENV PRIVATE_TASKS=/tasks/
ENV PRIVATE_TASKS_BY_UID=/tasks/uid/
ENV PRIVATE_TASKS_BY_ID=/tasks/id/

ENV PRIVATE_OUTPUT_ZIPS_BY_ID=/outputs/id/
ENV PRIVATE_OUTPUT_ZIPS_BY_UID=/outputs/uid/

ENV PRIVATE_INPUT_ZIPS_BY_ID=/inputs/id/
ENV PRIVATE_INPUT_ZIPS_BY_UID=/inputs/uid/

ENV PRIVATE_MODELS=/models/
ENV PRIVATE_MODELS_BY_ID=/models/id/
ENV PRIVATE_MODELS_BY_UID=/models/uid/
ENV PRIVATE_MODELS_BY_HUMAN_READABLE_ID=/models/human_readable_id/
ENV PRIVATE_MODEL_ZIPS_BY_ID=/models/zip/uid/

CMD python main.py
