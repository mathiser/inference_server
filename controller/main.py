import logging
import os
import secrets
import tempfile

import uvicorn

from api.api_fastapi_impl import APIFastAPIImpl
from database.db_sql_impl import DBSQLiteImpl
from message_queue.rabbit_mq_impl import MQRabbitImpl
from typing import Union

def generate_token(bits=128):
    return secrets.token_urlsafe(bits)

class Controller:
    def __init__(self,
                 TZ: Union[str, None] = "Europe/Copenhagen",
                 DATA_DIR: Union[str, None] = "data",
                 RABBIT_HOSTNAME: Union[str, None] = "localhost",
                 RABBIT_PORT: Union[int, None] = 5672,
                 CONTROLLER_PORT: Union[int, None] = 8123,
                 LOG_LEVEL: Union[int, None] = 10,
                 INFERENCE_SERVER_TOKEN: Union[str, None] = None):

        self.TZ = TZ
        self.DATA_DIR = DATA_DIR
        
        self.RABBIT_HOSTNAME = RABBIT_HOSTNAME
        self.RABBIT_PORT = RABBIT_PORT

        self.CONTROLLER_PORT = CONTROLLER_PORT
        
        self.LOG_LEVEL = LOG_LEVEL
        self.INFERENCE_SERVER_TOKEN = INFERENCE_SERVER_TOKEN
        
        # Override from os.environ
        for name in self.__dict__.keys():
            if name in os.environ.keys():
                self.__setattr__(name, os.environ[name])
        
        if not self.INFERENCE_SERVER_TOKEN:
            self.INFERENCE_SERVER_TOKEN = generate_token()

        # Set logger
        LOG_FORMAT = '%(levelname)s:%(asctime)s:%(message)s'
        logging.basicConfig(level=int(self.LOG_LEVEL), format=LOG_FORMAT)
        self.logger = logging.getLogger(__name__)
                
        self.logger.info(f"INFERENCE_SERVER_TOKEN: {self.INFERENCE_SERVER_TOKEN}")
        self.logger.info("Make sure to sync this to all consumers")

    def run(self):
        mq = MQRabbitImpl(host=self.RABBIT_HOSTNAME,
                          port=int(self.RABBIT_PORT),
                          unfinished_queue_name="UNFINISHED_JOB_QUEUE",
                          finished_queue_name="FINISHED_JOB_QUEUE",
                          log_level=int(self.LOG_LEVEL))

        db = DBSQLiteImpl(base_dir=self.DATA_DIR, log_level=int(self.LOG_LEVEL))
        api = APIFastAPIImpl(db=db, mq=mq, x_token=self.INFERENCE_SERVER_TOKEN, log_level=int(self.LOG_LEVEL))
        uvicorn.run(app=api, host="0.0.0.0", port=self.CONTROLLER_PORT)

if __name__ == "__main__":
    m = Controller()
    m.run()