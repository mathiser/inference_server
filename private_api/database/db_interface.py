from abc import ABC, abstractmethod
from typing import List, BinaryIO, Optional

from .models import Task, Model


class DBInterface(ABC):
    @abstractmethod
    def add_task(cls,
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
    def add_model(cls,
                    container_tag: str,
                    human_readable_id: str,
                    input_mountpoint: str,
                    output_mountpoint: str,
                    zip_file: BinaryIO,
                    model_mountpoint: Optional[str] = None,
                    description: Optional[str] = None,
                    model_available: Optional[bool] = True,
                    use_gpu: Optional[bool] = True,
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
    def post_output_by_uid(cls, uid: str, zip_file: BinaryIO) -> Task:
        pass

