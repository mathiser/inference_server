import tempfile
from abc import ABC, abstractmethod
from typing import BinaryIO

from interfaces.db_models import Task, Model


class DBInterface(ABC):
    @abstractmethod
    def get_task(cls, uid: str) -> Task:
        pass

    @abstractmethod
    def get_input_zip(cls, uid: str) -> tempfile.TemporaryFile:
        pass

    @abstractmethod
    def get_model(cls, uid: str) -> Model:
        pass

    @abstractmethod
    def set_task_status(cls, uid: str, status: int):
        pass

    @abstractmethod
    def get_model_by_human_readable_id(cls, human_readable_id: str) -> Model:
        pass

    @abstractmethod
    def get_model_zip(cls, uid: str) -> tempfile.TemporaryFile:
        pass

    @abstractmethod
    def post_output(cls, uid: str, zip_file: BinaryIO) -> Task:
        pass
