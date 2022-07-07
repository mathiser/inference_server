import json
import logging
import os
import secrets
import tempfile
import threading
from typing import BinaryIO, Union, Optional
from urllib.parse import urljoin

from database.db_interface import DBInterface
from database_client.db_client_interface import DBClientInterface
from exceptions.exceptions import PostTaskException, TaskOutputZipNotFound, PostModelException

from models.models import Model


class DBImpl(DBInterface):
    def __init__(self, db_client: DBClientInterface):
        self.db_client = db_client

    def post_task(self,
                  model_human_readable_id: str,
                  zip_file: BinaryIO,
                  uid=None):

        if not uid:
            uid = secrets.token_urlsafe(32)

        params = {
            "model_human_readable_id": model_human_readable_id,
            "uid": uid
        }
        files = {"zip_file": zip_file}
        url = os.environ.get("POST_TASK")

        logging.info(f"[ ] Posting task: {params}")
        res = self.db_client.post(url=url, files=files, params=params)
        if not res.ok:
            logging.error(res.content)
            raise PostTaskException
        else:
            logging.info(f"[X] Posting task: {params}")
            return params

    def get_output_zip_by_uid(self, uid: str):
        # Zip the output for return
        logging.info(f"[ ]: Get output from task: {uid}")
        url = urljoin(os.environ['GET_OUTPUT_ZIP_BY_UID'], f"{uid}")
        res = self.db_client.get(url)

        logging.info(f"[X]: Get output from task: {uid}")
        return res

    def delete_task_by_by_uid(self, uid: str):
        # Zip the output for return
        logging.info(f"[ ]: Delete task: {uid}")
        url = urljoin(os.environ['GET_OUTPUT_ZIP_BY_UID'], f"{uid}")
        res = self.db_client.delete(url)

        logging.info(f"[X]: Delete task: {uid}")
        return res

    def post_model(self,
                   container_tag: str,
                   human_readable_id: str,
                   input_mountpoint: Union[str, None] = None,
                   output_mountpoint: Union[str, None] = None,
                   model_mountpoint: Union[str, None] = None,
                   description: Union[str, None] = None,
                   model_available: Union[bool, None] = None,
                   use_gpu: Union[bool, None] = None,
                   zip_file: Optional[Union[BinaryIO, None]] = None,
                   ):

        params = {
            "container_tag": container_tag,
            "human_readable_id": human_readable_id,
            "input_mountpoint": input_mountpoint,
            "output_mountpoint": output_mountpoint,
            "model_mountpoint": model_mountpoint,
            "description": description,
            "model_available": model_available,
            "use_gpu": use_gpu
        }
        files = {"zip_file": zip_file}
        url = os.environ.get("POST_MODEL")

        if zip_file:
            res = self.db_client.post(url, files=files, params=params)
        else:
            res = self.db_client.post(url, params=params)

        if not res.ok:
            logging.error(res.content)
            raise PostModelException
        else:
            logging.info(f"[X] Posting task: {params}")
            return params

    def get_models(self):
        url = os.environ["GET_MODELS"]
        res = self.db_client.get(url)
        logging.info(res)
        return [Model(**m) for m in json.loads(res.content)]
