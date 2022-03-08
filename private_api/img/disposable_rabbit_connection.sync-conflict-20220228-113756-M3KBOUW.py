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
    def __init__(self, host, exchange, queue, body):
        while True:
            try:
                # Try connect to RabbitMQ
                super().__init__(pika.ConnectionParameters(host=host))
                break
            except Exception as e:
                logging.error(e)

        # Establish channel
        self.channel = self.channel()
        self.channel.queue_declare(queue=queue, durable=True)
        
        ## Publish job
        self.channel.basic_publish(exchange=exchange, routing_key=queue, body=body)
        self.close()



