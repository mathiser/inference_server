FROM python:3.10-buster
ADD requirements.txt /requirements.txt
#RUN apt-get update
RUN pip install -r /requirements.txt
COPY main.py /main.py
RUN mkdir /data
ENV LOG_LEVEL=10
ENV VOLUME_MOUNTPOINT="/data"
CMD python3 /main.py