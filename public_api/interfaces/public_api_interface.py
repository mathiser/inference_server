from abc import abstractmethod
from typing import Optional, Any, Dict, List

from fastapi import File, UploadFile, FastAPI
from fastapi.responses import StreamingResponse

from interfaces.db_interface import DBInterface


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
                             zip_file: UploadFile = File(...)
                             ) -> str:
            pass

        @abstractmethod
        def public_get_output_zip(uid: str) -> StreamingResponse:
            pass

        @abstractmethod
        def public_delete_task(uid: str) -> Dict:
            pass

        @abstractmethod
        def public_post_model(container_tag: str,
                              human_readable_id: str,
                              description: Optional[str] = None,
                              zip_file: Optional[UploadFile] = File(None),
                              model_available: Optional[bool] = True,
                              use_gpu: Optional[bool] = True,
                              ) -> Dict:
            pass

        @abstractmethod
        def public_get_models() -> List:
            pass
