FROM python:3.10-buster
RUN apt-get update

ADD ../../requirements.txt /requirements.txt
RUN pip install -r /requirements.txt

COPY .. /opt/tests
WORKDIR /opt/tests
CMD ["/usr/local/bin/python", "-m", "unittest",  "private_api/test_private_api.py"]
