from abc import ABC, abstractmethod
from typing import Optional, List, BinaryIO, Union

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
    def post_output_zip_by_uid(cls, uid: str, zip_file: BinaryIO) -> Task:
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
    def get_model_by_id(cls, id: int) -> Model:
        pass

    @abstractmethod
    def get_model_by_human_readable_id(cls, human_readable_id: str) -> Model:
        pass

    @abstractmethod
    def get_models(cls) -> List[Model]:
        pass
