from abc import ABC, abstractmethod
from io import BytesIO
from typing import List, Union

from database.db_models import Task, Model


class DBInterface(ABC):
    @abstractmethod
    def post_task(self,
                 tar_file: BytesIO,
                 human_readable_id: str) -> Task:
        pass

    @abstractmethod
    def get_task(self,
                 task_id: Union[int, None] = None,
                 task_uid: Union[str, None] = None) -> Task:
        pass

    @abstractmethod
    def delete_task(self, uid: str) -> Task:
        pass

    @abstractmethod
    def set_task_status(self, task_id: int, status: int) -> Task:
        pass

    @abstractmethod
    def get_tasks(self) -> List:
        pass

    @abstractmethod
    def post_model(self,
                   container_tag: str,
                   human_readable_id: str,
                   description: Union[str, None] = None,
                   tar_file: Union[BytesIO, None] = None,
                   model_available: Union[bool, None] = None,
                   use_gpu: Union[bool, None] = None,
                   dump_logs: Union[bool, None] = None,
                   pull_on_every_run: Union[bool, None] = None) -> Model:
        pass

    @abstractmethod
    def get_model(self,
                  model_id: Union[int, None] = None,
                  human_readable_id: Union[str, None] = None) -> Model:
        pass

    @abstractmethod
    def get_models(self) -> List:
        pass

    @abstractmethod
    def post_output_tar(self, task_id: int, tar_file: BytesIO) -> Task:
        pass

