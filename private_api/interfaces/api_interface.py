from abc import abstractmethod
from typing import Union, List, Dict

from fastapi import File, UploadFile
from starlette.responses import FileResponse

from interfaces.db_models import Task, Model


class APIInterface:
    @abstractmethod
    def __init__(self):
        @abstractmethod
        def hello_world() -> Dict:
            pass

        @abstractmethod
        def get_tasks() -> List[Task]:
            pass

        @abstractmethod
        def get_task(uid: str) -> Task:
            pass

        @abstractmethod
        def delete_task(uid: str) -> Task:
            pass

        @abstractmethod
        def set_task_status_by_id(uid: str, status: int) -> Task:
            pass

        @abstractmethod
        def post_task(model_human_readable_id: str,
                      zip_file: Union[UploadFile, None] = None,
                      uid: Union[str, None] = None) -> Task:
            pass

        @abstractmethod
        def get_input_zip_by_uid(uid: str) -> FileResponse:
            pass

        @abstractmethod
        def post_output_zip(uid: str,
                            zip_file: UploadFile = File(...)) -> Task:
            pass

        @abstractmethod
        def get_output_zip(uid: str) -> Task:
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
        def get_model(uid: str) -> Model:
            pass

        @abstractmethod
        def get_model_by_human_readable_id(human_readable_id: str) -> Model:
            pass

        @abstractmethod
        def get_models() -> List[Model]:
            pass

        @abstractmethod
        def get_model_zip(uid: str) -> FileResponse:
            pass
