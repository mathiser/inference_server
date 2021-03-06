import json
import logging
import os
import secrets
import tempfile
import threading
import traceback
from typing import Any, Optional, Union, Dict
from urllib.parse import urljoin

import requests
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse, Response

from database.db_interface import DBInterface
from exceptions.exceptions import PostTaskException, ZipFileMissingException, ZipFileShouldBeNoneException, TaskOutputZipNotFound
from public_api.public_api_interface import PublicFastAPIInterface

app = FastAPI()

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

        @self.post(os.environ['PUBLIC_POST_TASK'])
        def public_post_task(model_human_readable_id: str,
                             zip_file: UploadFile,
                             ) -> str:

            models = self.db.get_models()
            if not model_human_readable_id in [model.human_readable_id for model in models]:
                raise HTTPException(550, detail="ModelNotFound")

            def post_task_thread(uid, model_human_readable_id, zip_file, ):
                logging.info(f"[ ] Posting task: {uid} on {model_human_readable_id}")
                return self.db.post_task(model_human_readable_id=model_human_readable_id,
                                         zip_file=zip_file,
                                         uid=uid)

            uid = secrets.token_urlsafe(32)  # Give this request a unique identifie}
            t = threading.Thread(target=post_task_thread, kwargs={"uid": uid,
                                                                  "model_human_readable_id": model_human_readable_id,
                                                                  "zip_file": zip_file.file})
            t.start()
            self.threads.append(t)
            return uid

        @self.get(urljoin(os.environ['PUBLIC_GET_OUTPUT_ZIP_BY_UID'], "{uid}"))
        def public_get_output_zip_by_uid(uid: str) -> StreamingResponse:
            def iterfile(bytes_from_db: bytes):
                with tempfile.TemporaryFile() as tmp_file:
                    tmp_file.write(bytes_from_db)
                    tmp_file.seek(0)
                    yield from tmp_file

            res = self.db.get_output_zip_by_uid(uid)

            if res.ok:
                return StreamingResponse(iterfile(bytes_from_db=res.content))
            else:
                try:
                    res.raise_for_status()
                except requests.HTTPError:
                    raise HTTPException(status_code=res.status_code, detail=json.loads(res.content))

        @self.delete(urljoin(os.environ['PUBLIC_GET_OUTPUT_ZIP_BY_UID'], "{uid}"))
        def public_delete_task_by_uid(uid: str):
            status = self.db.delete_task_by_uid(uid)

            try:
                return status
            except Exception as e:
                traceback.print_exc()
                raise HTTPException(status_code=550, detail=str(e))

        @self.get(os.environ["PUBLIC_GET_MODELS"])
        def public_get_models():
            try:
                return self.db.get_models()
            except Exception as e:
                raise HTTPException(status_code=550, detail=str(e))

        if bool(os.environ.get("ALLOW_PUBLIC_POST_MODEL")):
            @self.post(os.environ.get("PUBLIC_POST_MODEL"))
            def public_post_model(container_tag: str,
                                  human_readable_id: str,
                                  input_mountpoint: Union[str, None] = None,
                                  output_mountpoint: Union[str, None] = None,
                                  model_mountpoint: Union[str, None] = None,
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
                                              input_mountpoint=input_mountpoint,
                                              output_mountpoint=output_mountpoint,
                                              model_mountpoint=model_mountpoint,
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
