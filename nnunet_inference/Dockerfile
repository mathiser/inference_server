FROM nvcr.io/nvidia/pytorch:21.07-py3
RUN apt-get update

ADD requirements.txt /requirements.txt
RUN pip install -r /requirements.txt

ENV CODE="/opt/app/api"
ENV DATA="/opt/app/data" 
ENV MODEL="/opt/app/models"
ENV HOST="0.0.0.0"
ENV PORT="8000"
RUN mkdir -p $CODE $DATA $MODELS
WORKDIR $CODE
COPY . $CODE
