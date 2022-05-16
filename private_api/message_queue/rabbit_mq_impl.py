import logging
import os
import time

import pika

from database import DBInterface
from message_queue import MQInterface

from database import Task

LOG_FORMAT = ('%(levelname) -10s %(asctime)s %(name) -30s %(funcName) '
              '-35s %(lineno) -5d: %(message)s')
LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)



class MQRabbitImpl(MQInterface):
    def __init__(self, host: str, db: DBInterface):
        self.host = host
        self.db = db
        self.unfinished_queue_name = os.environ["UNFINISHED_JOB_QUEUE"]
        self.finished_queue_name = os.environ["FINISHED_JOB_QUEUE"]
        self.connection = None
        self.channel = None
        while True:
            try:
                self.connection = pika.BlockingConnection(pika.ConnectionParameters(self.host))
                if self.connection.is_open:
                    self.channel = self.connection.channel()
                    self.unfinished_queue = self.declare_queue(self.unfinished_queue_name)
                    self.finished_queue = self.declare_queue(self.finished_queue_name)
                    break
            except Exception as e:
                logging.error(f"Could not connect to RabbitMQ - is it running? Expecting it on {os.environ.get('RABBIT_HOST')}:{os.environ.get('RABBIT_PORT')}")
                time.sleep(10)

    def __del__(self):
        if self.channel:
            self.channel.close()
        if self.connection:
            self.connection.close()

    def declare_queue(self, queue: str):
        return self.channel.queue_declare(queue=queue, durable=True)

    def publish_unfinished_task(self, task: Task):
        return self.channel.basic_publish(exchange="", routing_key=self.unfinished_queue_name, body=f"{task.uid}")

    def publish_finished_task(self, task: Task):
        return self.channel.basic_publish(exchange="", routing_key=self.finished_queue_name, body=f"{task.uid}")


    def get_from_queue(self, queue_name):
        method_frame, header_frame, body = self.channel.basic_get(queue_name)
        if method_frame:
            return method_frame, header_frame, body
        else:
            return None

    def ack_method_frame(self, method_frame):
        return self.channel.basic_ack(method_frame.delivery_tag)



