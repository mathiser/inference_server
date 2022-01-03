import atexit
import logging
import os
from time import sleep

import pika

LOG_FORMAT = ('%(levelname) -10s %(asctime)s %(name) -30s %(funcName) '
              '-35s %(lineno) -5d: %(message)s')
LOGGER = logging.getLogger(__name__)

logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)

class DisposablePikaConnection(pika.BlockingConnection):
    def __init__(self, host, exchange, queue,  body, uid):
        while True:
            try:
                super().__init__(pika.ConnectionParameters(host=host))
                logging.info(f"[X] {uid}: Successfully connected to {host}")
                break
            except Exception as e:
                logging.error(e)
        
        self.channel = self.channel()
        self.channel.queue_declare(queue=queue, durable=True)
        
        ## Publish job
        logging.info(f"[ ] {uid}: Publishing message {body} to {queue} on {host}")
        self.channel.basic_publish(exchange=exchange, routing_key=queue, body=body)
        logging.info(f"[X] {uid}: Publishing message {body} to {queue} on {host}")

        logging.info(f"[ ] {uid}: Closing connection on {host}")
        self.close()
        logging.info(f"[ ] {uid}: Closing connection on {host}")
        


