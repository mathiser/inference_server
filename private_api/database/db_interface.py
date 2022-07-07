from abc import ABC, abstractmethod
from typing import List, BinaryIO, Optional, Union

from .models import Task, Model


class DBInterface(ABC):
    @abstractmethod
    def post_task(self,
                 zip_file: BinaryIO,
                 model_human_readable_id: str,
                 uid: str) -> Task:
        pass

    @abstractmethod
    def get_task_by_id(self, id: int) -> Task:
        pass

    @abstractmethod
    def get_task_by_uid(self, uid: str) -> Task:
        pass

    @abstractmethod
    def delete_task_by_uid(self, uid: str) -> Task:
        pass

    @abstractmethod
    def set_task_status_by_uid(self, uid: str, status: int) -> Task:
        pass

    @abstractmethod
    def get_tasks(self) -> List[Task]:
        pass

    @abstractmethod
    def post_model(self,
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
    def get_model_by_id(self, id: int) -> Model:
        pass

    @abstractmethod
    def get_models(self) -> List[Model]:
        pass

    @abstractmethod
    def post_output_zip_by_uid(self, uid: str, zip_file: BinaryIO) -> Task:
        pass

