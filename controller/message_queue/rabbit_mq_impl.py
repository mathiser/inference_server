import logging
import time

import pika
from database.db_models import Task
from message_queue.mq_interface import MQInterface
from message_queue.mq_exceptions import PublishTaskException

class MQRabbitImpl(MQInterface):
    def __init__(self, host: str, port: int, unfinished_queue_name: str, finished_queue_name: str, log_level=10):
        LOG_FORMAT = '%(levelname)s:%(asctime)s:%(message)s'
        logging.basicConfig(level=log_level, format=LOG_FORMAT)
        self.logger = logging.getLogger(__name__)

        self.host = host
        self.port = port
        self.unfinished_queue_name = unfinished_queue_name
        self.finished_queue_name = finished_queue_name

    def get_connection_and_channel(self):
        connection = None
        channel = None
        while True:
            try:
                connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.host, port=self.port))
                channel = connection.channel()
                if channel.is_open:
                    channel.queue_declare(queue=self.unfinished_queue_name, durable=True)
                    channel.queue_declare(queue=self.finished_queue_name, durable=True)
                    return connection, channel
            except Exception as e:
                self.logger.error(f"Could not connect to RabbitMQ - is it running? Expecting it on {self.host}:{self.port}")
                time.sleep(10)

    def close(self, connection, channel):
        if channel.is_open:
            channel.close()
        if connection.is_open:
            connection.close()

    def publish_unfinished_task(self, task: Task):
        conn, chan = self.get_connection_and_channel()
        try:
            chan.basic_publish(exchange="", routing_key=self.unfinished_queue_name, body=f"{task.id}")
        except Exception as e:
            self.logger.error(e)
            raise PublishTaskException

        self.close(conn, chan)

    def publish_finished_task(self, task: Task):
        conn, chan = self.get_connection_and_channel()
        try:
            chan.basic_publish(exchange="", routing_key=self.finished_queue_name, body=f"{task.uid}")
        except Exception as e:
            self.logger.error(e)
            raise PublishTaskException

        self.close(conn, chan)


