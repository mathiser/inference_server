import logging
from abc import abstractmethod
from typing import Optional, Any, Dict

from fastapi import File, UploadFile, FastAPI
from fastapi.responses import StreamingResponse, Response
from database.db_interface import DBInterface

class PublicFastAPIInterface(FastAPI):
    @abstractmethod
    def __init__(self,
                 db: DBInterface,
                 **extra: Any):
        super().__init__(**extra)
        self.db = db

        @abstractmethod
        def public_hello_world():
            pass

        @abstractmethod
        def public_post_task(model_human_readable_id: str,
                      zip_file: UploadFile = File(...),
                      uid=None) -> str:
            pass

        @abstractmethod
        def public_get_output_zip_by_uid(uid: str) -> StreamingResponse:
            pass

        @abstractmethod
        def public_delete_task_by_uid(uid: str):
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
                       ):
            pass

        @abstractmethod
        def public_get_models():
            pass
