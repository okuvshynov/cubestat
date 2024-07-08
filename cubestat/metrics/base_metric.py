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

    # configure metric instance
    def configure(self, config):
        return self

    # if we define any options to select/toggle view mode
    @classmethod
    def configure_argparse(cls, parser):
        pass

    @classmethod
    @abstractmethod
    def key(cls):
        pass
