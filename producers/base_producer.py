from abc import ABC, abstractmethod


class BaseProducer(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def produce(self):
        pass
