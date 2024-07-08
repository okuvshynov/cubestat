from abc import ABC, abstractmethod

class base_metric(ABC):
    @abstractmethod
    def read(self, context):
        pass

    @abstractmethod
    def pre(self, mode, title):
        pass

    @abstractmethod
    def format(self, values, idxs):
        pass

    def configure(self, config):
        return self

    @classmethod
    @abstractmethod
    def key(cls):
        pass
