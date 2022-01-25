FROM python:3.9-buster

ADD requirements.txt /requirements.txt
RUN pip install -r /requirements.txt

RUN mkdir /opt/app/
COPY . /opt/app/
WORKDIR /opt/app/