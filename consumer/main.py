import logging
import os
from typing import Union

from message_queue.consumer_rabbitmq_impl import ConsumerRabbitImpl
from database.database_rest_impl import DBRestImpl
from database_client.db_client_requests_impl import DBClientRequestsImpl


class Consumer:

    def __init__(self,
                 TZ: Union[str, None] = "Europe/Copenhagen",
                 RABBIT_HOSTNAME: Union[str, None] = "localhost",
                 RABBIT_PORT: Union[int, None] = 5672,
                 CONTROLLER_HOSTNAME: Union[str, None] = "localhost",
                 CONTROLLER_PORT: Union[int, None] = 8123,
                 HTTPS: Union[bool, None] = False,
                 PREFETCH_VALUE: Union[int, None] = 1,
                 GPU_UUID: Union[str, None] = None,
                 LOG_LEVEL: Union[str, None] = 10,
                 INFERENCE_SERVER_TOKEN: Union[str, None] = None):
        self.TZ = TZ
        self.RABBIT_HOSTNAME = RABBIT_HOSTNAME
        self.RABBIT_PORT = RABBIT_PORT
        self.PREFETCH_VALUE = PREFETCH_VALUE
        self.GPU_UUID = GPU_UUID
        if HTTPS:
            prot = "https"
        else:
            prot = "http"
        self.CONTROLLER_URL = f"{prot}://{CONTROLLER_HOSTNAME}:{CONTROLLER_PORT}"
        self.LOG_LEVEL = LOG_LEVEL
        self.INFERENCE_SERVER_TOKEN = INFERENCE_SERVER_TOKEN

        self.logger = self.get_logger()
        self.load_envvars()

        if not self.INFERENCE_SERVER_TOKEN:
            raise Exception("INFERENCE_SERVER_TOKEN not in environment. Make sure to set this and try again")

        self.db_client = DBClientRequestsImpl(base_url=self.CONTROLLER_URL, x_token=self.INFERENCE_SERVER_TOKEN)
        self.db = DBRestImpl(db_client=self.db_client)
        self.consumer = ConsumerRabbitImpl(self.RABBIT_HOSTNAME,
                                           port=int(self.RABBIT_PORT),
                                           db=self.db,
                                           unfinished_queue_name="UNFINISHED_JOB_QUEUE",
                                           finished_queue_name="FINISHED_JOB_QUEUE",
                                           prefetch_value=int(self.PREFETCH_VALUE),
                                           gpu_uuid=self.GPU_UUID)

    def run(self):
        self.consumer.consume_unfinished()

    def load_envvars(self):
        # Override from os.environ
        for name in self.__dict__.keys():
            if name in os.environ.keys():
                self.logger.info(f"Overwriting {name} to {os.environ[name]}")
                self.__setattr__(name, os.environ[name])

    def get_logger(self):
        # Set logger
        LOG_FORMAT = '%(levelname)s:%(asctime)s:%(message)s'
        logging.basicConfig(level=int(self.LOG_LEVEL), format=LOG_FORMAT)
        return logging.getLogger(__name__)

if __name__ == "__main__":
    m = Consumer()
    m.run()
