import atexit
import os
from time import sleep

import pika
import logging

while True:
    try:
        logging.info(f"Connecting to rabbit host: {os.environ['RABBIT_HOST']}")
        rabbit_connection = pika.BlockingConnection(pika.ConnectionParameters(host=os.environ["RABBIT_HOST"]))
        rabbit_channel = rabbit_connection.channel()
        logging.info(f"Connection successful to rabbit host: {os.environ['RABBIT_HOST']}")
        break
    except Exception as e:
        logging.error(e)
        sleep(1)

rabbit_channel.queue_declare(queue=os.environ["UNFINISHED_JOB_QUEUE"], durable=True)

# Release connection on exit
atexit.register(rabbit_connection.close)