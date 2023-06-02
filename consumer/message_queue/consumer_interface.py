from abc import ABC, abstractmethod


class ConsumerInterface(ABC):
    @abstractmethod
    def consume_unfinished(self):
        pass

