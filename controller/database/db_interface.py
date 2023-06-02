from abc import ABC, abstractmethod
from typing import List, BinaryIO, Union

from interfaces.db_models import Task, Model


class DBInterface(ABC):
    @abstractmethod
    def post_task(self,
                 zip_file: BinaryIO,
                 model_human_readable_id: str,
                 uid: str) -> Task:
        pass

    @abstractmethod
    def get_task(self, uid: str) -> Task:
        pass

    @abstractmethod
    def delete_task(self, uid: str) -> Task:
        pass

    @abstractmethod
    def set_task_status(self, uid: str, status: int) -> Task:
        pass

    @abstractmethod
    def get_tasks(self) -> List[Task]:
        pass

    @abstractmethod
    def post_model(self,
                   container_tag: str,
                   human_readable_id: str,
                   description: Union[str, None] = None,
                   zip_file: Union[BinaryIO, None] = None,
                   model_available: Union[bool, None] = None,
                   use_gpu: Union[bool, None] = None
                   ) -> Model:
        pass

    @abstractmethod
    def get_model(self,
                  uid: Union[str, None] = None,
                  human_readable_id: Union[str, None] = None) -> Model:
        pass

    @abstractmethod
    def get_models(self) -> List[Model]:
        pass

    @abstractmethod
    def post_output_zip(self, uid: str, zip_file: BinaryIO) -> Task:
        pass

