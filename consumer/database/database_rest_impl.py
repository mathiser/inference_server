import logging
import os
from io import BytesIO

from database.database_interface import DBInterface
from database.db_models import Task
from database_client.db_client_interface import DBClientInterface


class DBRestImpl(DBInterface):
    def __init__(self, db_client: DBClientInterface, log_level=10):
        self.db_client = db_client
        self.task_endpoint = "/api/tasks/"
        self.input_endpoint = "/api/tasks/inputs/"
        self.output_endpoint = "/api/tasks/outputs/"
        self.model_endpoint = "/api/models/"
        self.model_tar_endpoint = "/api/models/tars/"
        self.log_level = log_level
        self.logger = self.get_logger()
        
    def get_logger(self):
        # Set logger
        LOG_FORMAT = '%(levelname)s:%(asctime)s:%(message)s'
        logging.basicConfig(level=self.log_level, format=LOG_FORMAT)
        return logging.getLogger(__name__)

    def get_task(self, task_id: int) -> Task:
        res = self.db_client.get(url=self.task_endpoint,
                                 params={"task_id": task_id})
        res.raise_for_status()
        return Task(**res.json())

    def get_input_tar(self, task_id: int) -> BytesIO:
        res = self.db_client.get(url=self.input_endpoint,
                                 params={"task_id": task_id})
        res.raise_for_status()
        return BytesIO(res.content)

    def get_model_tar(self, model_id: int) -> BytesIO:
        res = self.db_client.get(url=self.model_tar_endpoint,
                                 params={"model_id": model_id})
        res.raise_for_status()
        return BytesIO(res.content)

    def post_output_tar(self, task_id: int, tar_file: BytesIO) -> Task:
        res = self.db_client.post(self.output_endpoint,
                                  params={"task_id": task_id},
                                  files={"tar_file": tar_file})

        print(res, res.json())
        res.raise_for_status()
        return Task(**res.json())

    def set_task_status(self, task_id: int, status: int) -> Task:
        res = self.db_client.put(self.task_endpoint,
                                 params={"task_id": task_id,
                                         "status": status})
        res.raise_for_status()
        return Task(**res.json())
