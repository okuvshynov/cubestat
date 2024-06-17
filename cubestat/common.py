from enum import Enum

class EnumLoop(Enum):
    def next(self):
        values = list(self.__class__)
        return values[(values.index(self) + 1) % len(values)]
    
    def prev(self):
        values = list(self.__class__)
        return values[(values.index(self) + len(values) - 1) % len(values)]
    
class EnumStr(Enum):
    def __str__(self):
        return self.value

class CPUMode(EnumLoop, EnumStr):
    all = 'all'
    by_cluster = 'by_cluster'
    by_core = 'by_core'

class SimpleMode(EnumLoop, EnumStr):
    show = 'show'
    hide = 'hide'

class RateReader:
    def __init__(self, interval_ms):
        self.interval_s = interval_ms / 1000.0
        self.last = {}

    def next(self, key, value):
        if key not in self.last.keys():
            self.last[key] = value
        res = (value - self.last[key]) / self.interval_s
        self.last[key] = value
        return res