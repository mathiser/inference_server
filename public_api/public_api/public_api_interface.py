import logging
from abc import abstractmethod
from typing import Optional, Any

from fastapi import File, UploadFile, FastAPI
from fastapi.responses import StreamingResponse, Response
from database.db_interface import DBInterface

LOG_FORMAT = '%(levelname)s:%(asctime)s:%(message)s'

logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)

class PublicFastAPIInterface(FastAPI):
    @abstractmethod
    def __init__(self,
                 db: DBInterface,
                 **extra: Any):
        super().__init__(**extra)
        self.db = db

        @abstractmethod
        def public_hello_world() -> Response:
            pass

        @abstractmethod
        def public_post_task(model_human_readable_id: str,
                      zip_file: UploadFile = File(...),
                      uid=None) -> Response:
            pass

        @abstractmethod
        def public_get_output_zip_by_uid(uid: str) -> StreamingResponse:
            pass

        @abstractmethod
        def public_post_model(container_tag: str,
                       human_readable_id: str,
                       input_mountpoint: Optional[str] = None,
                       output_mountpoint: Optional[str] = None,
                       model_mountpoint: Optional[str] = None,
                       description: Optional[str] = None,
                       zip_file: Optional[UploadFile] = File(None),
                       model_available: Optional[bool] = True,
                       use_gpu: Optional[bool] = True,
                       ) -> Response:
            pass

        @abstractmethod
        def public_get_models() -> Response:
            pass
