FROM python:3.10-buster
RUN apt-get update

ADD requirements.txt /requirements.txt
RUN pip install -r /requirements.txt

COPY . /opt/tests
WORKDIR /opt/tests

RUN cat cert.crt >> /usr/local/lib/python3.10/site-packages/certifi/cacert.pem
RUN cat /usr/local/lib/python3.10/site-packages/certifi/cacert.pem
CMD ["/usr/local/bin/python", "-m", "unittest",  "test_public_api.py"]
