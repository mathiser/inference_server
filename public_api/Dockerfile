FROM python:3.9-buster

ADD requirements.txt /requirements.txt
RUN pip install -r /requirements.txt

RUN mkdir /opt/app/
COPY . /opt/app/
WORKDIR /opt/app/
ENV TZ=Europe/Copenhagen


ENV TZ=Europe/Copenhagen
ENV RABBIT_DOCKER_TAG=rabbitmq:3.9.17

ENV API_HOSTNAME=private_api
ENV API_PORT=7000
ENV API_URL=http://private_api:7000

ENV LOG_LEVEL=20

ENV API_TASKS=/api/tasks/
ENV API_OUTPUT_ZIPS=/api/tasks/outputs/
ENV API_MODELS=/api/models/

ENV PUBLIC_API_HOSTNAME=public_api
ENV PUBLIC_API_PORT=8000