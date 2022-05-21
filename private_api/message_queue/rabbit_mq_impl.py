import logging
import os
import time

import pika

from database import Task

LOG_FORMAT = ('%(levelname) -10s %(asctime)s %(name) -30s %(funcName) '
              '-35s %(lineno) -5d: %(message)s')
LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)



class MQRabbitImpl(MQInterface):
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.unfinished_queue_name = os.environ["UNFINISHED_JOB_QUEUE"]
        self.finished_queue_name = os.environ["FINISHED_JOB_QUEUE"]

    def get_connection_and_channel(self):
        connection = None
        channel = None
        while True:
            connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.host, port=self.port))
            if connection.is_open:
                channel = connection.channel()
                channel.queue_declare(queue=self.unfinished_queue_name, durable=True)
                channel.queue_declare(queue=self.finished_queue_name, durable=True)

                return connection, channel
            else:
                logging.error(f"Could not connect to RabbitMQ - is it running? Expecting it on {self.host}:{self.port}")
                time.sleep(10)

    def close(self, connection, channel):
        if channel.is_open:
            channel.close()
        if connection.is_open:
            connection.close()

    def publish_unfinished_task(self, task: Task):
        conn, chan = self.get_connection_and_channel()
        chan.basic_publish(exchange="", routing_key=self.unfinished_queue_name, body=f"{task.uid}")
        self.close(conn, chan)

    def publish_finished_task(self, task: Task):
        conn, chan = self.get_connection_and_channel()
        chan.basic_publish(exchange="", routing_key=self.finished_queue_name, body=f"{task.uid}")
        self.close(conn, chan)

    def get_from_queue(self, queue_name):
        method_frame, header_frame, body = self.channel.basic_get(queue_name)
        if method_frame:
            return method_frame, header_frame, body
        else:
            return None

    def ack_method_frame(self, method_frame):
        return self.channel.basic_ack(method_frame.delivery_tag)



