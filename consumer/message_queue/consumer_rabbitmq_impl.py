import atexit
import functools
import logging
import os
import threading
import time
import traceback
from typing import Union

import docker
import pika

from database.database_interface import DBInterface
from docker_helper import volume_functions
from job.job_docker_functions import exec_job
from message_queue.consumer_interface import ConsumerInterface


class ConsumerRabbitImpl(ConsumerInterface):
    def __init__(self,
                 host: str,
                 port: int,
                 db: DBInterface,
                 unfinished_queue_name: str,
                 finished_queue_name: str,
                 prefetch_value: int,
                 gpu_uuid: Union[str, None] = None,
                 log_level: int = 10
                 ):
        self.host = host
        self.port = port
        self.db = db
        self.threads = []
        self.unfinished_queue_name = unfinished_queue_name
        self.finished_queue_name = finished_queue_name
        self.connection = None
        self.channel = None
        self.prefetch_value = prefetch_value
        self.cli = docker.from_env()
        self.gpu_uuid = gpu_uuid
        self.log_level = log_level
        self.logger = self.get_logger()
        # Close things on exit
        exit_func = functools.partial(self.on_exit, self.threads, self.connection, self.cli)
        atexit.register(exit_func)

    def get_logger(self):
        # Set logger
        LOG_FORMAT = '%(levelname)s:%(asctime)s:%(message)s'
        logging.basicConfig(level=self.log_level, format=LOG_FORMAT)
        return logging.getLogger(__name__)

    def set_connection_and_channel(self):
        while True:
            try:
                self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.host, port=self.port))
                self.channel = self.connection.channel()
                if self.channel.is_open:
                    self.channel.queue_declare(queue=self.unfinished_queue_name, durable=True)
                    self.channel.queue_declare(queue=self.finished_queue_name, durable=True)
                    break
            except Exception as e:
                self.logger.info(f"Could not connect to RabbitMQ - is it running? Expecting it on {self.host}:{self.port}")
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
        if not self.connection or not self.channel:
            self.set_connection_and_channel()

        self.logger.info(f": Setting RabbitMQ prefetch_count to {self.prefetch_value}")
        self.channel.basic_qos(prefetch_count=self.prefetch_value)

        on_message_callback = functools.partial(self.on_message, args=(self.connection, self.threads))
        self.channel.basic_consume(queue=self.unfinished_queue_name, on_message_callback=on_message_callback)

        self.logger.info(' [*] Waiting for messages')
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
        self.logger.info(fmt1.format(thread_id, delivery_tag, body))
        task_id = body.decode()

        try:
            # Parse body to get task id to run
            task = self.db.get_task(task_id=task_id)
            self.logger.info(f"Getting input_tar for task: {task.dict()}")
            task_input_tar = self.db.get_input_tar(task.id)
            if not volume_functions.volume_exists(task.model.model_volume_id) and task.model.model_available:
                self.logger.info(f"Creating model volume for: {task.model.dict()}")
                volume_functions.create_empty_volume(volume_id=task.model.model_volume_id)
                model_tar = self.db.get_model_tar(task.model.id)
            else:
                model_tar = None

            self.logger.info(f"Running task: {task.dict()}")
            self.db.set_task_status(task_id=task.id, status=2)  # Set status to running
            output_tar = exec_job(task=task,
                                  input_tar=task_input_tar,
                                  model_tar=model_tar,
                                  gpu_uuid=self.gpu_uuid)

            self.db.post_output_tar(task.id, output_tar)

        except Exception as e:
            self.db.set_task_status(task_id=task_id, status=0)
            traceback.print_exc()
            self.logger.info(f"Exception {str(e)} while running: {task.id}")

            raise e

        finally:
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
        if conn:
            conn.close()
        if cli:
            cli.close()
