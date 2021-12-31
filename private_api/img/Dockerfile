FROM python:3.10-buster

ADD requirements.txt /requirements.txt
RUN pip install -r /requirements.txt

RUN mkdir -p /opt/app/ /opt/app/data/
COPY . /opt/app/
WORKDIR /opt/app/