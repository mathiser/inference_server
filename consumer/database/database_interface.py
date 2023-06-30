import tempfile
from abc import ABC, abstractmethod
from io import BytesIO
from typing import BinaryIO

from database.db_models import Task, Model


class DBInterface(ABC):
    @abstractmethod
    def get_task(cls, task_id: int) -> Task:
        pass

    @abstractmethod
    def get_input_tar(cls, task_id: int) -> BytesIO:
        pass


    @abstractmethod
    def set_task_status(cls, task_id: int, status: int):
        pass


    @abstractmethod
    def get_model_tar(cls, model_id: int) -> BytesIO:
        pass

    @abstractmethod
    def post_output_tar(cls, task_id: int, tar_file: BinaryIO) -> Task:
        pass
