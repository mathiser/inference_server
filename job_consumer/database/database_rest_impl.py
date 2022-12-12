import json
import logging
import os
import tempfile
from typing import BinaryIO
from urllib.parse import urljoin

import requests

from interfaces.database_interface import DBInterface
from interfaces.db_client_interface import DBClientInterface
from interfaces.db_models import Model, Task

LOG_FORMAT = '%(levelname)s:%(asctime)s:%(message)s'
logging.basicConfig(level=int(os.environ.get("LOG_LEVEL")), format=LOG_FORMAT)


class DBRestImpl(DBInterface):
    def __init__(self, db_client: DBClientInterface):
        self.db_client = db_client

    def get_task(self, uid: str) -> Task:
        res = self.db_client.get(urljoin(os.environ["API_TASKS"], uid))
        return Task(**res.json())

    def get_input_zip(self, uid: str) -> BinaryIO:
        res = self.db_client.get(urljoin(os.environ["API_INPUT_ZIPS"], str(uid)), stream=True)
        if not res.ok:
            logging.error(f"RES not ok: {res}")
            raise Exception(res.content)

        return self.res_to_tmp_file(res)

    def get_model(self, uid: str) -> Model:
        res = self.db_client.get(urljoin(os.environ["API_MODELS"], str(uid)))
        return Model(**res.json())

    def get_model_by_human_readable_id(self, human_readable_id: str) -> Model:
        res = self.db_client.get(urljoin(os.environ["API_MODELS_BY_HUMAN_READABLE_ID"], str(human_readable_id)))
        return Model(**json.loads(res.content))

    def get_model_zip(self, uid: str) -> tempfile.TemporaryFile:
        res = self.db_client.get(urljoin(os.environ["API_MODEL_ZIPS"], str(uid)), stream=True)
        res.raise_for_status()
        return self.res_to_tmp_file(res)

    def post_output(self, uid: str, zip_file: BinaryIO) -> Model:
        res = self.db_client.post(urljoin(os.environ['API_OUTPUT_ZIPS'], uid),
                                  files={"zip_file": zip_file})

        return Model(**res.json())

    def set_task_status(self, uid: str, status: int):
        return self.db_client.put(os.environ["POST_TASK"],
                                  params={"uid": uid,
                                          "status": status})

    def res_to_tmp_file(self, res) -> tempfile.TemporaryFile:
        if not res.ok:
            logging.error(f"RES not ok: {res}")
            raise Exception(res.content)

        tmp_file = tempfile.TemporaryFile()
        tmp_file.write(res.content)
        tmp_file.seek(0)
        return tmp_file
