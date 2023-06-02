import logging
import os
from io import BytesIO

from database.database_interface import DBInterface
from database.db_models import Task
from database_client.db_client_interface import DBClientInterface

LOG_FORMAT = '%(levelname)s:%(asctime)s:%(message)s'
logging.basicConfig(level=int(os.environ.get("LOG_LEVEL")), format=LOG_FORMAT)


class DBRestImpl(DBInterface):
    def __init__(self, db_client: DBClientInterface):
        self.db_client = db_client
        self.task_endpoint = "/api/task/"
        self.input_endpoint = "/api/task/input/"
        self.output_endpoint = "/api/task/output/"
        self.model_endpoint = "/api/model/"
        self.model_zip_endpoint = "/api/model/zip"

    def get_task(self, uid: str) -> Task:
        res = self.db_client.get(url=self.task_endpoint,
                                 params={"uid": uid})
        res.raise_for_status()
        return Task(**res.json())

    def get_input_zip(self, uid: str) -> BytesIO:
        res = self.db_client.get(url=self.input_endpoint,
                                 params={"uid": uid})
        res.raise_for_status()
        return BytesIO(res.json())

    def get_model_zip(self, uid: str) -> BytesIO:
        res = self.db_client.get(url=self.model_zip_endpoint,
                                 params={"uid": uid})
        res.raise_for_status()
        return BytesIO(res.json())

    def post_output_zip(self, uid: str, zip_file: BytesIO) -> Task:
        res = self.db_client.post(self.output_endpoint,
                                  params={"uid": uid},
                                  files={"zip_file": zip_file})
        res.raise_for_status()
        return Task(**res.json())

    def set_task_status(self, uid: str, status: int) -> Task:
        res = self.db_client.put(self.task_endpoint,
                                 params={"uid": uid,
                                         "status": status})
        res.raise_for_status()
        return Task(**res.json())
