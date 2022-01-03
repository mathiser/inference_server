FROM python:3.10-buster

ADD requirements.txt /requirements.txt
RUN pip install -r /requirements.txt

RUN mkdir -p /opt/app/
WORKDIR /opt/app/
COPY . /opt/app/

CMD python -u main.py