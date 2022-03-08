import logging
import os
import time

import pika

LOG_FORMAT = ('%(levelname)s:%(asctime)s:%(message)s')
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)

counter = 0
while counter < 120:
    try:
        logging.info(f": Connecting to rabbit host: {os.environ['RABBIT_HOST']}")
        # Note: sending a short heartbeat to prove that heartbeats are still
        # sent even though the worker simulates long-running work
        rabbit_connection = pika.BlockingConnection(pika.ConnectionParameters(host=os.environ["RABBIT_HOST"]))
        rabbit_channel = rabbit_connection.channel()

        logging.info(f": Declaring queue: {os.environ['UNFINISHED_JOB_QUEUE']} on {os.environ['RABBIT_HOST']}")
        rabbit_channel.queue_declare(queue=os.environ["UNFINISHED_JOB_QUEUE"], durable=True)

        prefetch_val = 1
        logging.info(f": Setting RabbitMQ prefetch_count to {prefetch_val}")
        rabbit_channel.basic_qos(prefetch_count=prefetch_val)
        break
    except Exception as e:
        logging.error(e)
        logging.error("Failed to connect to RabbitMQ. Timeout 1 sec and try again")
        time.sleep(1)
        counter += 1