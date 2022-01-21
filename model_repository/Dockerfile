FROM python:3.10-buster
RUN apt-get update

ADD requirements.txt /requirements.txt
RUN pip install -r /requirements.txt

COPY main.py /main.py

CMD ["/usr/local/bin/python", "-u", "/main.py"]
