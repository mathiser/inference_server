FROM python:3.10-buster
ADD requirements.txt /requirements.txt
RUN apt-get update
RUN pip install -r /requirements.txt
COPY main.py /main.py
CMD python3 /main.py