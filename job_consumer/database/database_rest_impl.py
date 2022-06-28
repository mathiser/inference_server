import json
import logging
import os
import tempfile
from typing import BinaryIO
from urllib.parse import urljoin

import requests

from .database_interface import DBInterface
from .models import Model, Task

LOG_FORMAT = '%(levelname)s:%(asctime)s:%(message)s'
logging.basicConfig(level=int(os.environ.get("LOG_LEVEL")), format=LOG_FORMAT)


class DBRestImpl(DBInterface):
    def __init__(self, api_url):
        self.api_url = api_url
        
    def get_task_by_uid(self, uid: str) -> Task:
        res = requests.get(self.api_url + urljoin(os.environ["GET_TASK_BY_UID"], uid))
        return Task(**json.loads(res.content))

    def get_input_zip_by_id(self, id: int) -> BinaryIO:
        res = requests.get(self.api_url + urljoin(os.environ["GET_INPUT_ZIP_BY_ID"], str(id)), stream=True)
        if not res.ok:
            logging.error(f"RES not ok: {res}")
            raise Exception(res.content)

        return self.res_to_tmp_file(res)

    def get_model_by_id(self, id: int) -> Model:
        res = requests.get(self.api_url + urljoin(os.environ["GET_MODEL_BY_ID"], str(id)))
        return Model(**json.loads(res.content))

    def get_model_by_human_readable_id(self, human_readable_id: str) -> Model:
        res = requests.get(self.api_url + urljoin(os.environ["GET_MODEL_BY_HUMAN_READABLE_ID"], str(human_readable_id)))
        return Model(**json.loads(res.content))

    def get_model_zip_by_id(self, id: int) -> tempfile.TemporaryFile:
        res = requests.get(self.api_url + urljoin(os.environ["GET_MODEL_ZIP_BY_ID"], str(id)), stream=True)
        if not res.ok:
            logging.error(f"RES not ok: {res}")
            raise Exception(res.content)
        return self.res_to_tmp_file(res)

    def post_output_by_uid(self, uid: str, zip_file: BinaryIO) -> Model:
        res = requests.post(self.api_url + urljoin(os.environ['POST_OUTPUT_ZIP_BY_UID'], uid),
                            files={"zip_file": zip_file})

        return Model(**res.json())

    def set_task_status_by_uid(self, uid: str, status: int):
        return requests.put(url=urljoin(self.api_url, os.environ["POST_TASK"]),
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