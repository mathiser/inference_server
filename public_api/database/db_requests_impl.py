import json
import logging
import os
import secrets
import tempfile
import threading
from typing import BinaryIO, Union
from urllib.parse import urljoin

from database.db_interface import DBInterface
from database_client.db_client_interface import DBClientInterface
from exceptions.db_exceptions import PostTaskException, TaskOutputZipNotFound


class DBRequestsImpl(DBInterface):
    def __init__(self, db_client: DBClientInterface):
        self.db_client = db_client
        self.threads = []

    def __del__(self):
        for t in self.threads:
            t.join()

    def post_task(self,
                  model_human_readable_id: str,
                  zip_file: BinaryIO,
                  uid=None):
        if not uid:
            uid = secrets.token_urlsafe(32)

        # Give this request a unique identifier
        def post_task_thread(url, zip_file_from_res, params):
            logging.info(f"[ ] Posting task: {params}")
            res = self.db_client.post(url=url, files={"zip_file": zip_file_from_res}, params=params)
            if not res.ok:
                logging.error(res.content)
                raise PostTaskException
            else:
                logging.info(f"[X] Posting task: {params}")

        params = {
            "model_human_readable_id": model_human_readable_id,
            "uid": uid
        }

        url = os.environ.get("POST_TASK")
        t = threading.Thread(target=post_task_thread, args=(url, zip_file, params))
        t.start()
        t.join()  ## For syncronous exec - need to find a fix
        self.threads.append(t)
        return params

    def get_output_zip_by_uid(self, uid: str) -> tempfile.TemporaryFile:
        # Zip the output for return
        logging.info(f"[ ]: Get output from task: {uid}")
        url = urljoin(os.environ['GET_OUTPUT_ZIP_BY_UID'], f"{uid}")
        res = self.db_client.get(url, stream=True)

        if not res.ok:
            raise TaskOutputZipNotFound

        else:
            logging.info(f"[X]: Get output from task: {uid}")
            tmp_file = tempfile.TemporaryFile()
            for chunk in res.iter_content(1000000):
                tmp_file.write(chunk)
            tmp_file.seek(0)

            return tmp_file

    def post_model(self,
                   container_tag: str,
                   human_readable_id: str,
                   input_mountpoint: Union[str, None] = None,
                   output_mountpoint: Union[str, None] = None,
                   model_mountpoint: Union[str, None] = None,
                   description: Union[str, None] = None,
                   model_available: Union[bool, None] = None,
                   use_gpu: Union[bool, None] = None,
                   zip_file: Union[BinaryIO, None] = None,
                   ):

        # Give this request a unique identifier
        def post_task_thread(url, zip_file_from_res, params):
            res = self.db_client.post(url, files={"zip_file": zip_file_from_res}, params=params)
            if not res.ok:
                logging.error(res.content)
                raise PostTaskException
            else:
                logging.info(f"[X] Posting task: {params}")
                return res

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
        url = os.environ.get("POST_MODEL")
        t = threading.Thread(target=post_task_thread, args=(url, zip_file, params))
        t.start()
        t.join()  ## For syncronous exec - need to find a fix
        self.threads.append(t)
        return params

    def get_models(self):
        url = os.environ["GET_MODELS"]
        res = self.db_client.get(url)
        logging.info(res)
        return json.loads(res.content)
