from abc import abstractmethod
from abc import abstractmethod
from typing import Any, Union, List, Dict

from database.models import Task, Model
from fastapi import File, UploadFile
from starlette.responses import FileResponse

from private_api.database import DBInterface
from private_api.message_queue import MQInterface


class APIInterface():
    def __init__(self, db: DBInterface, mq: MQInterface, **extra: Any):
        super().__init__(**extra)
        self.db = db
        self.mq = mq

        @abstractmethod
        def hello_world() -> Dict:
            pass

        @abstractmethod
        def get_tasks() -> List[Task]:
            pass

        @abstractmethod
        def get_task_by_id(id: int) -> Task:
            pass

        @abstractmethod
        def get_task_by_uid(uid: str) -> Task:
            pass

        @abstractmethod
        def post_task(model_human_readable_id: str,
                      zip_file: Union[UploadFile, None] = None,
                      uid: Union[str, None] = None) -> Task:
            pass

        @abstractmethod
        def get_input_zip_by_id(id: int) -> FileResponse:
            pass

        @abstractmethod
        def post_output_zip_by_uid(uid: str,
                                   zip_file: UploadFile = File(...)) -> Task:
            pass

        @abstractmethod
        def get_output_zip_by_uid(uid: str) -> Task:
            pass

        @abstractmethod
        def post_model(container_tag: str,
                       human_readable_id: str,
                       input_mountpoint: Union[str, None] = None,
                       output_mountpoint: Union[str, None] = None,
                       model_mountpoint: Union[str, None] = None,
                       description: Union[str, None] = None,
                       zip_file: Union[UploadFile, None] = None,
                       model_available: Union[bool, None] = None,
                       use_gpu: Union[bool, None] = None,
                       ) -> Model:
            pass

        @abstractmethod
        def get_model_by_id(id: int) -> Model:
            pass

        @abstractmethod
        def get_model_by_human_readable_id(human_readable_id: str) -> Model:
            pass

        @abstractmethod
        def get_models() -> List[Model]:
            pass

        @abstractmethod
        def get_model_zip_by_id(id: int) -> FileResponse:
            pass
