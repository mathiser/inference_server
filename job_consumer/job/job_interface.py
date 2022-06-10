from abc import ABC, abstractmethod

from database.models import Model, Task


class JobInterface(ABC):
    @abstractmethod
    def __init__(cls) -> None:
        pass

    @abstractmethod
    def set_model(self, model: Model):
        pass

    @abstractmethod
    def set_task(self, task: Task):
        pass

    @abstractmethod
    def send_volume_output(cls):
        pass

    @abstractmethod
    def execute(cls):
        pass