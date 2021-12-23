FROM nvcr.io/nvidia/pytorch:21.07-py3
RUN apt-get update

ADD requirements.txt /requirements.txt
RUN pip install -r /requirements.txt

RUN mkdir -p /opt/app/api /opt/app/data /opt/app/models
WORKDIR /opt/app/api
COPY . /opt/app/api

EXPOSE 8000

ENTRYPOINT ["bash", "-c",  "uvicorn api:app", "--reload"]
