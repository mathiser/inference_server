FROM mathiser/nnunet:nnunet_base
RUN apt-get update && apt-get install -y \
    rsync \
    && rm -rf /var/lib/apt/lists/*

COPY . /

ENV INPUT=/input
ENV OUTPUT=/output
ENV RESULTS_FOLDER=/model

RUN mkdir $INPUT $OUTPUT $RESULTS_FOLDER

RUN ["chmod", "+x", "/main.sh"]
CMD ["bash", "-c", "/main.sh"]
