from abc import ABC, abstractmethod


class JobInterface(ABC):
    @abstractmethod
    def __init__(cls) -> None:
        pass
    @abstractmethod
    def execute(cls):
        pass