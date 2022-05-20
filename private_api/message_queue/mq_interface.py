from abc import ABC, abstractmethod

from database.models import Task


class MQInterface(ABC):
    @abstractmethod
    def publish_unfinished_task(cls, task: Task):
        pass

    @abstractmethod
    def publish_finished_task(cls, task: Task):
        pass

