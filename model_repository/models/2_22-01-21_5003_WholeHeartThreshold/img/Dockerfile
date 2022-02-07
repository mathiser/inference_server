FROM mathiser/nnunet:nnunet_base

COPY . /
ENV INPUT=/input
ENV OUTPUT=/output
ENV RESULTS_FOLDER=/model

RUN mkdir $INPUT $OUTPUT $RESULTS_FOLDER 



RUN ["chmod", "+x", "/main.sh"]

CMD ["bash", "-c", "/main.sh"]
