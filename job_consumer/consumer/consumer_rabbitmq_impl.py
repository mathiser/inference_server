import atexit
import functools
import logging
import os
import threading
import time

import docker
import pika
from database.database_interface import DBInterface
from job.job_interface import JobInterface

from .consumer_interface import ConsumerInterface

LOG_FORMAT = ('%(levelname) -10s %(asctime)s %(name) -30s %(funcName) '
              '-35s %(lineno) -5d: %(message)s')
LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)


class ConsumerRabbitImpl(ConsumerInterface):
    def __init__(self, host: str, port: int, db: DBInterface, JobClass: JobInterface):
        self.host = host
        self.port = port
        self.db = db
        self.JobClass = JobClass  # JobImplementation - to be instantiated repeatedly
        self.threads = []
        self.unfinished_queue_name = os.environ["UNFINISHED_JOB_QUEUE"]
        self.finished_queue_name = os.environ["FINISHED_JOB_QUEUE"]
        self.connection = None
        self.channel = None
        self.cli = docker.from_env()

        # Attempt connection to Rabbit
        while True:
            try:
                self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.host, port=self.port))
                if self.connection.is_open:
                    self.channel = self.connection.channel()
                    self.unfinished_queue = self.declare_queue(self.unfinished_queue_name)
                    self.finished_queue = self.declare_queue(self.finished_queue_name)
                    break
            except Exception as e:
                logging.error(f"Could not connect to RabbitMQ - is it running? Expecting it on {self.host}:{self.port}")
                time.sleep(10)

        # Close things on exit
        exit_func = functools.partial(self.on_exit, self.threads, self.connection, self.cli)
        atexit.register(exit_func)

    def get_connection_and_channel(self):
        while True:
            self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.host, port=self.port))
            if self.connection.is_open:
                self.channel = self.connection.channel()
                self.declare_queue(self.unfinished_queue_name)
                self.declare_queue(self.finished_queue_name)
                return
            else:
                logging.error(f"Could not connect to RabbitMQ - is it running? Expecting it on {self.host}:{self.port}")
                time.sleep(10)


    def close(self):
        if self.channel.is_open:
            self.channel.close()
        if self.connection.is_open:
            self.connection.close()
        self.cli.close()

    def declare_queue(self, queue: str):
        return self.channel.queue_declare(queue=queue, durable=True)

    def consume_unfinished(self):
        on_message_callback = functools.partial(self.on_message, args=(self.connection, self.threads))
        self.channel.basic_consume(queue=self.unfinished_queue_name, on_message_callback=on_message_callback)

        logging.info(' [*] Waiting for messages')
        self.channel.start_consuming()

    def on_message(self, channel, method_frame, header_frame, body, args):
        (connection, threads) = args
        delivery_tag = method_frame.delivery_tag
        t = threading.Thread(target=self.do_work, args=(self.connection, channel, delivery_tag, body))
        t.start()
        threads.append(t)

    def do_work(self, connection, channel, delivery_tag, body):
        thread_id = threading.get_ident()
        fmt1: str = 'Thread id: {} Delivery tag: {} Message body: {}'
        logging.info(fmt1.format(thread_id, delivery_tag, body))

        # Parse body to get task uid to run
        uid = body.decode()
        task = self.db.get_task_by_uid(uid)
        model = self.db.get_model_by_human_readable_id(task.model_human_readable_id)

        # Execute task - function handles dispatchment of docker jobs.
        j = self.JobClass(db=self.db)
        j.set_task(task=task)
        j.set_model(model=model)
        j.execute()
        j.send_volume_output()
        del j

        # Acknowledgement callback
        cb = functools.partial(self.ack_message, channel, delivery_tag)
        connection.add_callback_threadsafe(cb)

    def ack_message(self, channel, delivery_tag):
        if self.channel.is_open:
            channel.basic_ack(delivery_tag)
        else:
            raise Exception("Channel closed - Y tho?")

    def on_exit(self, threads, conn, cli):
        for thread in threads:
            thread.join()

        conn.close()
        cli.close()