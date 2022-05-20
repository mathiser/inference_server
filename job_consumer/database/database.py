import logging
from typing import BinaryIO

from requests import Response

from .database_interface import DBInterface
from .models import Model, Task
from .database_rest_impl import DBRestImpl

LOG_FORMAT = '%(levelname)s:%(asctime)s:%(message)s'
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)


class DB(DBInterface):
    def __init__(self, api_url):
        self.api_url = api_url
        self.db = DBRestImpl(self.api_url)

    def get_task_by_uid(self, uid: str) -> Task:
        return self.db.get_task_by_uid(uid=uid)

    def get_input_zip_by_id(self, id: int) -> BinaryIO:
        return self.db.get_input_zip_by_id(id=id)

    def get_model_by_id(self, id: int) -> Model:
        return self.db.get_model_by_id(id=id)

    def get_model_by_human_readable_id(self, human_readable_id: str) -> Model:
        return self.db.get_model_by_human_readable_id(human_readable_id=human_readable_id)

    def get_model_zip_by_id(self, id: int) -> BinaryIO:
        return self.db.get_model_zip_by_id(id=id)

    def post_output_by_uid(self, uid: str, zip_file: BinaryIO) -> Model:
        return self.db.post_output_by_uid(uid=uid, zip_file=zip_file)