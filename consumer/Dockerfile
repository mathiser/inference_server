FROM ubuntu:20.04
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    docker.io \
    && rm -rf /var/lib/apt/lists/*

ADD requirements.txt requirements.txt
RUN pip install -r requirements.txt

RUN mkdir -p /home/app/
WORKDIR /home/app/
COPY . /home/app/

CMD python3 main.py
