from abc import ABC, abstractmethod
from typing import List, BinaryIO, Optional, Union

from .models import Task, Model


class DBInterface(ABC):
    @abstractmethod
    def post_task(cls,
                 zip_file: BinaryIO,
                 model_human_readable_id: str,
                 uid: str) -> Task:
        pass

    @abstractmethod
    def get_task_by_id(cls, id: int) -> Task:
        pass

    @abstractmethod
    def get_task_by_uid(cls, uid: str) -> Task:
        pass

    @abstractmethod
    def get_tasks(cls) -> List[Task]:
        pass

    @abstractmethod
    def post_model(cls,
                   container_tag: str,
                   human_readable_id: str,
                   input_mountpoint: Union[str, None] = None,
                   output_mountpoint: Union[str, None] = None,
                   model_mountpoint: Union[str, None] = None,
                   description: Union[str, None] = None,
                   zip_file: Union[BinaryIO, None] = None,
                   model_available: Union[bool, None] = None,
                   use_gpu: Union[bool, None] = None

                   ) -> Model:
        pass

    @abstractmethod
    def get_model_by_human_readable_id(self, human_readable_id: str) -> Model:
        pass

    @abstractmethod
    def get_model_by_id(cls, id: int) -> Model:
        pass

    @abstractmethod
    def get_models(cls) -> List[Model]:
        pass

    @abstractmethod
    def post_output_zip_by_uid(cls, uid: str, zip_file: BinaryIO) -> Task:
        pass

