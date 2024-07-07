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

    @classmethod
    @abstractmethod
    def supported_platforms(cls):
        pass
 
    @classmethod
    @abstractmethod
    def key(cls):
        pass
