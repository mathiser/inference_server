import logging
import time

import pika
import os
import functools
while True:
    try:
        logging.info(f"[ ]: Connecting to rabbit host: {os.environ['RABBIT_HOST']}")
        # Note: sending a short heartbeat to prove that heartbeats are still
        # sent even though the worker simulates long-running work
        rabbit_connection = pika.BlockingConnection(pika.ConnectionParameters(host=os.environ["RABBIT_HOST"]))
        rabbit_channel = rabbit_connection.channel()
        logging.info(f"[X]: Connecting to rabbit host: {os.environ['RABBIT_HOST']}")

        logging.info(f"[ ]: Declaring queue: {os.environ['UNFINISHED_JOB_QUEUE']} on {os.environ['RABBIT_HOST']}")
        rabbit_channel.queue_declare(queue=os.environ["UNFINISHED_JOB_QUEUE"], durable=True)
        logging.info(f"[ ]: Declaring queue: {os.environ['UNFINISHED_JOB_QUEUE']} on {os.environ['RABBIT_HOST']}")

        prefetch_val = 1
        rabbit_channel.basic_qos(prefetch_count=prefetch_val)
        logging.info(f"[X]: RabbitMQ prefetch_count set to {prefetch_val}")
        break
    except Exception as e:
        logging.error(e)
        logging.error("Failed to connect to RabbitMQ. Timeout 1 sec and try again")
        time.sleep(1)