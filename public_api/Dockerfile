FROM python:3.9-buster

ADD requirements.txt /requirements.txt
RUN pip install -r /requirements.txt

RUN mkdir /opt/app/
COPY . /opt/app/
WORKDIR /opt/app/

ENV ALLOW_PUBLIC_POST_MODEL=""
ENV LOG_LEVEL=20
ENV PUBLIC_TASKS=/tasks/
ENV PUBLIC_MODELS=/models/

ENV PRIVATE_TASKS=/tasks/
ENV PRIVATE_TASK_BY_UID=/tasks/uid/
ENV PRIVATE_TASK_BY_ID=/tasks/id/

ENV PRIVATE_OUTPUT_ZIPS_BY_ID=/outputs/id/
ENV PRIVATE_OUTPUT_ZIPS_BY_UID=/outputs/uid/

ENV PRIVATE_INPUT_ZIPS_BY_ID=/inputs/id/
ENV PRIVATE_INPUT_ZIPS_BY_UID=/inputs/uid/

## A task is the context with which to run a container on an input
ENV PRIVATE_MODELS=/models/
ENV PRIVATE_MODEL_BY_ID=/models/id/
ENV PRIVATE_MODEL_BY_UID=/models/uid/
ENV PRIVATE_MODEL_BY_HUMAN_READABLE_ID=/models/human_readable_id/
ENV PRIVATE_MODEL_ZIPS_BY_ID=/models/zip/uid/

CMD python main.py