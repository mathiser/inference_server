FROM python:3.9-buster
ADD requirements.txt requirements.txt
RUN pip install -r requirements.txt

RUN mkdir -p /home/app/
WORKDIR /home/app/

COPY . /home/app/

CMD python3 main.py
