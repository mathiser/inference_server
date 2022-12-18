import json
import logging
import os

import secrets
from typing import BinaryIO, Union, Optional
from urllib.parse import urljoin

from interfaces.db_client_interface import DBClientInterface
from interfaces.db_interface import DBInterface
from interfaces.db_models import Model


class DBImpl(DBInterface):
    def __init__(self, db_client: DBClientInterface):
        self.db_client = db_client

    def post_task(self,
                  model_human_readable_id: str,
                  zip_file: BinaryIO,
                  uid: str):

        params = {
            "model_human_readable_id": model_human_readable_id,
            "uid": uid
        }
        files = {"zip_file": zip_file}
        url = os.environ.get("API_TASKS")

        logging.info(f"[ ] Posting task: {params}")
        res = self.db_client.post(url=url, files=files, params=params)
        res.raise_for_status()
        logging.info(f"[X] Posting task: {params}")
        return params

    def get_output_zip(self, uid: str):
        # Zip the output for return
        logging.info(f"[ ]: Get output from task: {uid}")
        url = urljoin(os.environ['API_OUTPUT_ZIPS'], f"{uid}")
        res = self.db_client.get(url)

        logging.info(f"[X]: Get output from task: {uid}")
        return res

    def delete_task(self, uid: str):
        # Zip the output for return
        logging.info(f"[ ]: Delete task: {uid}")
        url = urljoin(os.environ['API_TASKS'], f"{uid}")
        res = self.db_client.delete(url)
        logging.info(f"[X]: Delete task: {uid}")

        return res

    def post_model(self,
                   container_tag: str,
                   human_readable_id: str,
                   description: Union[str, None] = None,
                   model_available: Union[bool, None] = None,
                   use_gpu: Union[bool, None] = None,
                   zip_file: Optional[Union[BinaryIO, None]] = None,
                   ):

        params = {
            "container_tag": container_tag,
            "human_readable_id": human_readable_id,
            "description": description,
            "model_available": model_available,
            "use_gpu": use_gpu
        }
        if zip_file:
            files = {"zip_file": zip_file}
        else:
            files = None
        url = os.environ.get("API_MODELS")
        res = self.db_client.post(url, files=files, params=params)
        logging.error(res.content)
        res.raise_for_status()

        logging.info(f"[X] Posting task: {params}")
        return res.json()

    def get_models(self):
        url = os.environ["API_MODELS"]
        res = self.db_client.get(url)
        logging.info(res)
        return [Model(**m) for m in json.loads(res.content)]
