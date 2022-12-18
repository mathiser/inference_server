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
from pika import exceptions

from interfaces.database_interface import DBInterface
from job.job_docker_impl import JobDockerImpl
from interfaces.consumer_interface import ConsumerInterface

LOG_FORMAT = ('%(levelname) -10s %(asctime)s %(name) -30s %(funcName) '
              '-35s %(lineno) -5d: %(message)s')
LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=int(os.environ.get("LOG_LEVEL")), format=LOG_FORMAT)


class ConsumerRabbitImpl(ConsumerInterface):
    def __init__(self,
                 host: str,
                 port: int,
                 db: DBInterface,
                 unfinished_queue_name: str,
                 finished_queue_name: str,
                 prefetch_value: int,
                 api_url: str,
                 api_output_zips: str,
                 volume_sender_docker_tag: str,
                 network_name: str,
                 gpu_uuid: Union[str, None] = None
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
        self.api_url = api_url
        self.api_output_zips = api_output_zips
        self.volume_sender_docker_tag = volume_sender_docker_tag
        self.network_name = network_name
        self.gpu_uuid = gpu_uuid

        # Close things on exit
        exit_func = functools.partial(self.on_exit, self.threads, self.connection, self.cli)
        atexit.register(exit_func)

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
                logging.info(f"Could not connect to RabbitMQ - is it running? Expecting it on {self.host}:{self.port}")
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

        logging.info(f": Setting RabbitMQ prefetch_count to {self.prefetch_value}")
        self.channel.basic_qos(prefetch_count=self.prefetch_value)

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
        uid = body.decode()

        try:
            # Parse body to get task uid to run
            task = self.db.get_task(uid)
            model = self.db.get_model_by_human_readable_id(task.model_human_readable_id)

            # Execute task
            j = JobDockerImpl(db=self.db,
                              api_url=self.api_url,
                              api_output_zips=self.api_output_zips,
                              volume_sender_docker_tag=self.volume_sender_docker_tag,
                              network_name=self.network_name,
                              gpu_uuid=self.gpu_uuid)
            j.set_task(task=task)
            j.set_model(model=model)

            self.db.set_task_status(uid=uid, status=2)  # Set status to running
            j.execute()
            j.send_volume_output()

        except Exception as e:
            self.db.set_task_status(uid=uid, status=0)
            traceback.print_exc()


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
