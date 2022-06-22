import tempfile
from abc import ABC, abstractmethod
from typing import BinaryIO

from requests import Response

from .models import Task, Model


class DBInterface(ABC):
    @abstractmethod
    def get_task_by_uid(cls, uid: str) -> Task:
        pass

    @abstractmethod
    def get_input_zip_by_id(cls, id: int) -> tempfile.TemporaryFile:
        pass

    @abstractmethod
    def get_model_by_id(cls, id: int) -> Model:
        pass

    @abstractmethod
    def set_task_status_by_uid(self, uid: str, status: int):
        pass

    @abstractmethod
    def get_model_by_human_readable_id(cls, human_readable_id: str) -> Model:
        pass

    @abstractmethod
    def get_model_zip_by_id(cls, id: int) -> tempfile.TemporaryFile:
        pass

    @abstractmethod
    def post_output_by_uid(cls, uid: str, zip_file: BinaryIO) -> Task:
        pass
