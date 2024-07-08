from abc import ABC, abstractmethod

from cubestat.common import SimpleMode

class base_metric(ABC):
    @abstractmethod
    def read(self, context):
        pass

    @abstractmethod
    def pre(self, title):
        pass

    @abstractmethod
    def format(self, values, idxs):
        pass

    # configure metric instance
    def configure(self, config):
        self.mode = SimpleMode.show
        return self

    # if we define any options to select/toggle view mode
    @classmethod
    def configure_argparse(cls, parser):
        pass

    @classmethod
    @abstractmethod
    def key(cls):
        pass

    def hotkey(self):
        return None
