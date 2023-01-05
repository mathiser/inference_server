FROM python:3.9-buster

ADD requirements.txt /requirements.txt
RUN pip install -r /requirements.txt

RUN mkdir /home/app/
COPY . /home/app/
WORKDIR /home/app/
ENV TZ=Europe/Copenhagen
ENV API_HOSTNAME=private_api
ENV API_PORT=7000
ENV API_URL=http://private_api:7000
ENV LOG_LEVEL=20
ENV API_TASKS=/api/tasks/
ENV API_OUTPUT_ZIPS=/api/tasks/outputs/
ENV API_MODELS=/api/models/
ENV PUBLIC_API_MODELS=/api/models/
ENV PUBLIC_API_TASKS=/api/tasks/
ENV PUBLIC_API_HOSTNAME=public_api
ENV PUBLIC_API_PORT=8000
ENV ALLOW_PUBLIC_POST_MODEL="true"
ENV PYTHONUNBUFFERED=1
EXPOSE $API_PORT
CMD python3 main.py
