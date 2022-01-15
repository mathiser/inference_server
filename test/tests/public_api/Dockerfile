FROM python:3.10-buster
RUN apt-get update

ADD requirements.txt /requirements.txt
RUN pip install -r /requirements.txt

COPY . /opt/tests
WORKDIR /opt/tests

ENV CERT_FILE=/opt/tests/certs.pem
ENV REQUESTS_CA_BUNDLE=""


CMD ["/usr/local/bin/python", "-m", "unittest",  "test_public_api.py"]
