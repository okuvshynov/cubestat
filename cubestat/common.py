import math
from enum import Enum

class DisplayMode(Enum):
    def __str__(self):
        return self.value

    def next(self):
        values = list(self.__class__)
        return values[(values.index(self) + 1) % len(values)]
    
    def prev(self):
        values = list(self.__class__)
        return values[(values.index(self) + len(values) - 1) % len(values)]
    
class SimpleMode(DisplayMode):
    show = 'show'
    hide = 'hide'

# buckets is a list of factor/label, e.g. [(1024*1024, 'Mb'), (1024, 'Kb'), (1, 'b')]
def format_measurement(curr, mx, buckets):
    for lim, unit in buckets[:-1]:
        if mx > lim:
            return f'{curr / lim :3.0f} {unit}'
    return f'{curr :3.0f} {buckets[-1][1]}'

def label2(slice, buckets, idxs):
    mx = max(slice)
    mx = float(1 if mx == 0 else 2 ** (int((mx - 1)).bit_length()))
    return mx, [format_measurement(slice[idx], mx, buckets) for idx in idxs]

def label10(slice, buckets, idxs):
    mx = max(slice)
    mx = float(1 if mx <= 0 else 10 ** math.ceil(math.log10(mx)))
    return mx, [format_measurement(slice[idx], mx, buckets) for idx in idxs]

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
