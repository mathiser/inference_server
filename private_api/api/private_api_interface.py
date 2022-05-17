from abc import ABC, abstractmethod
from typing import Optional, List, BinaryIO

from database import DBInterface, Task, Model
from message_queue import MQInterface


class PrivateAPIInterface(ABC):
    @abstractmethod
    def __init__(cls, db: DBInterface, mq: MQInterface):
        cls.db = db
        cls.mq = mq

    @abstractmethod
    def hello_world(cls):
        pass

    @abstractmethod
    def get_tasks(cls) -> List[Task]:
        pass

    @abstractmethod
    def get_task_by_id(cls, id: int) -> Task:
        pass

    @abstractmethod
    def get_task_by_uid(cls, uid: str) -> Task:
        pass

    @abstractmethod
    def post_task(cls,
                  human_readable_id: str,
                  zip_file: BinaryIO,
                  uid) -> Task:
        pass

    @abstractmethod
    def post_output_by_uid(cls, uid: str, zip_file: BinaryIO) -> Task:
        pass


    @abstractmethod
    def post_model(cls,
                   container_tag: str,
                   human_readable_id: str,
                   input_mountpoint: str,
                   output_mountpoint: str,
                   model_mountpoint: Optional[str] = None,
                   description: Optional[str] = None,
                   zip_file: Optional[BinaryIO] = None,
                   model_available: Optional[bool] = True,
                   use_gpu: Optional[bool] = True,
                   ) -> Model:
        pass

    @abstractmethod
    def get_model_by_id(cls, id: int) -> Model:
        pass

    @abstractmethod
    def get_models(cls) -> List[Model]:
        pass
