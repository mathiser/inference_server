from abc import ABC, abstractmethod

from database.db_models import Task


class MQInterface(ABC):
    @abstractmethod
    def publish_unfinished_task(self, task: Task):
        pass

    @abstractmethod
    def publish_finished_task(self, task: Task):
        pass

