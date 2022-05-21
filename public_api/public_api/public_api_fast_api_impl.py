import logging
import os
from typing import Any, Optional, Union
from urllib.parse import urljoin

from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse, Response

from database.db_interface import DBInterface
from public_api.public_api_interface import PublicFastAPIInterface

app = FastAPI()

threads = []

LOG_FORMAT = ('%(levelname)s:%(asctime)s:%(message)s')
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)


class PublicFastAPI(PublicFastAPIInterface):
    def __init__(self, db: DBInterface, **extra: Any):
        super().__init__(db=db, **extra)

        @self.get("/")
        def public_hello_world():
            return {"message": "Hello world - Welcome to the public database API"}

        @self.post(os.environ['PUBLIC_POST_TASK'])
        def public_post_task(model_human_readable_id: str,
                             zip_file: UploadFile,
                             ) -> Response:
            try:

                return self.db.post_task(model_human_readable_id=model_human_readable_id,
                                         zip_file=zip_file.file,
                                         )
            except Exception as e:
                raise e
        @self.get(urljoin(os.environ['PUBLIC_GET_OUTPUT_ZIP_BY_UID'], "{uid}"))
        def public_get_output_zip_by_uid(uid: str) -> StreamingResponse:
            try:
                with self.db.get_output_zip_by_uid(uid) as output_yield_from_tmp_file:
                    #def iterfile():
                    #    yield from output_tmp_file

                    return StreamingResponse(output_yield_from_tmp_file)
            except Exception as e:
                raise e
        @self.get(os.environ["PUBLIC_GET_MODELS"])
        def public_get_models():
            try:
                return self.db.get_models()
            except Exception as e:
                raise e

        @self.post(os.environ.get("PUBLIC_POST_MODEL"))
        def public_post_model(container_tag: str,
                              human_readable_id: str,
                              input_mountpoint: Union[str, None] = None,
                              output_mountpoint: Union[str, None] = None,
                              model_mountpoint: Union[str, None] = None,
                              description: Union[str, None] = None,
                              model_available: Union[bool, None] = None,
                              use_gpu: Union[bool, None] = None,
                              zip_file: Union[UploadFile, None] = None,
                              ):

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
                raise e