import json
import logging
import os
import secrets
import tempfile
import threading
import traceback
from typing import Any, Optional, Union
from urllib.parse import urljoin

import requests
from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.responses import StreamingResponse
from interfaces.public_api_interface import PublicFastAPIInterface

from exceptions.exceptions import ZipFileMissingException, ZipFileShouldBeNoneException
from interfaces.db_interface import DBInterface

threads = []

LOG_FORMAT = ('%(levelname)s:%(asctime)s:%(message)s')
logging.basicConfig(level=int(os.environ.get("LOG_LEVEL")), format=LOG_FORMAT)


class PublicFastAPI(PublicFastAPIInterface):
    def __init__(self, db: DBInterface, **extra: Any):
        super().__init__(db=db, **extra)
        self.threads = []

        @self.get("/")
        def public_hello_world():
            return {"message": "Hello world - Welcome to the public database API"}

        @self.post(os.environ['PUBLIC_API_TASKS'])
        def public_post_task(model_human_readable_id: str,
                             zip_file: UploadFile,
                             ) -> str:
            def post_task_thread(uid, model_human_readable_id, zip_file):
                logging.info(f"[ ] Posting task: {uid} on {model_human_readable_id}")
                try:
                    self.db.post_task(model_human_readable_id=model_human_readable_id,
                                            zip_file=zip_file,
                                            uid=uid)
                except Exception:
                    traceback.print_exc()
                finally:
                    zip_file.close()

            models = self.db.get_models()
            if not model_human_readable_id in [model["human_readable_id"] for model in models]:
                raise HTTPException(550, detail="ModelNotFound")

            uid = secrets.token_urlsafe()  # Give this request a unique identifie}
            tmp_zip_file = tempfile.TemporaryFile()
            tmp_zip_file.write(zip_file.file.read())
            tmp_zip_file.seek(0)
            t = threading.Thread(target=post_task_thread, kwargs={"uid": uid,
                                                                  "model_human_readable_id": model_human_readable_id,
                                                                  "zip_file": tmp_zip_file})
            t.start()
            self.threads.append(t)
            return uid

        @self.get(urljoin(os.environ['PUBLIC_API_TASKS'], "{uid}"))
        def public_get_output_zip_by_uid(uid: str) -> StreamingResponse:
            def iterfile(bytes_from_db: bytes):
                with tempfile.TemporaryFile() as tmp_file:
                    tmp_file.write(bytes_from_db)
                    tmp_file.seek(0)
                    yield from tmp_file

            res = self.db.get_output_zip(uid)
            print("HEEEEERERERERERER")
            logging.debug(res)

            if res.ok:
                return StreamingResponse(iterfile(bytes_from_db=res.content))
            else:
                try:
                    res.raise_for_status()
                except requests.HTTPError:
                    raise HTTPException(status_code=res.status_code, detail=json.loads(res.content))

        @self.delete(urljoin(os.environ['PUBLIC_API_TASKS'], "{uid}"))
        def public_delete_task_by_uid(uid: str):
            deleted_task = self.db.delete_task(uid)

            try:
                return deleted_task
            except Exception as e:
                logging.error(deleted_task)
                traceback.print_exc()
                raise HTTPException(status_code=550, detail=str(e))

        @self.get(os.environ["PUBLIC_API_MODELS"])
        def public_get_models():
            try:
                return self.db.get_models()
            except Exception as e:
                raise HTTPException(status_code=550, detail=str(e))

        if bool(os.environ.get("ALLOW_PUBLIC_POST_MODEL")):
            @self.post(os.environ.get("PUBLIC_API_MODELS"))
            def public_post_model(container_tag: str,
                                  human_readable_id: str,
                                  description: Union[str, None] = None,
                                  model_available: Union[bool, None] = None,
                                  use_gpu: Union[bool, None] = None,
                                  zip_file: Optional[Union[UploadFile, None]] = None,
                                  ):

                if model_available and not zip_file:
                    raise ZipFileMissingException
                if zip_file and not model_available:
                    raise ZipFileShouldBeNoneException

                if zip_file:
                    zip_file = zip_file.file

                try:
                    return self.db.post_model(container_tag=container_tag,
                                              human_readable_id=human_readable_id,
                                              description=description,
                                              zip_file=zip_file,
                                              model_available=model_available,
                                              use_gpu=use_gpu
                                              )
                except Exception as e:
                    logging.error(e)
                    raise e

    def __del__(self):
        for t in self.threads:
            t.join()
