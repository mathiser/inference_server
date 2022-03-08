FROM mathiser/nnunet:nnunet_base
RUN apt-get update

ADD requirements.txt /requirements.txt
RUN pip install -r /requirements.txt

RUN mkdir -p /opt/app

COPY . /opt/app/
WORKDIR /opt/app/

ENV INPUT=/input
ENV OUTPUT=/output
ENV RESULTS_FOLDER=/model

RUN mkdir $INPUT $OUTPUT $RESULTS_FOLDER

RUN ["chmod", "+x", "/opt/app/main.sh"]
CMD ["bash", "-c", "/opt/app/main.sh"]
