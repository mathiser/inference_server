FROM python:3.9-slim-buster
RUN apt-get update && apt-get install -y \
    dcm2niix \
    pigz \
    && rm -rf /var/lib/apt/lists/*

COPY main.py /main.py
RUN mkdir /input /output

ENTRYPOINT ["bash", "-c", "python3 -u /main.py /input /output"]