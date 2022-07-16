FROM python:3.9-buster

RUN apt-get update
ADD requirements.txt /requirements.txt
RUN pip install -r /requirements.txt

RUN mkdir -p /opt/app/ /opt/app/data/
COPY . /opt/app/
WORKDIR /opt/app/
ENV TZ=Europe/Copenhagen