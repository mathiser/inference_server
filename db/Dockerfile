FROM python:3.10-buster

RUN mkdir /opt/app/
RUN mkdir /opt/app/data/

COPY . /opt/app/
ADD requirements.txt /requirements.txt

RUN pip install -r /requirements.txt
WORKDIR /opt/app/