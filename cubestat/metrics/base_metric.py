from abc import ABC, abstractmethod

from cubestat.common import SimpleMode

# TODO: make this one metric_set or metric_group.
# each individual metric would be able to pick the implementation 
# for formatting, etc.
class base_metric(ABC):
    ###########################################################################
    # abstract methods each metric needs to implement
    ###########################################################################
    @abstractmethod
    def read(self, context):
        pass

    @abstractmethod
    def pre(self, title):
        pass

    @abstractmethod
    def format(self, title, values, idxs):
        pass

    @classmethod
    @abstractmethod
    def key(cls):
        pass

    ###########################################################################
    # methods with default implementation which each metric might override
    ###########################################################################

    # configure metric instance
    def configure(self, config):
        self.mode = SimpleMode.show
        return self

    # hotkey circle through the display modes
    def hotkey(self):
        return None

    # if we define any options to select/toggle view mode
    @classmethod
    def configure_argparse(cls, parser):
        pass

    # help message to be used for this metric. 
    @classmethod
    def help(self):
        return None
