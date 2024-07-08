import psutil

from cubestat.metrics.base_metric import base_metric
from cubestat.metrics.registry import cubestat_metric

@cubestat_metric
class ram_metric(base_metric):
    def read(self, _context):
        return {'RAM used %': psutil.virtual_memory().percent}
    
    def pre(self, mode, title):
        return True, ''
    
    def format(self, values, idxs):
        return 100.0, [f'{values[i]:3.0f}%' for i in idxs]

    @classmethod
    def key(cls):
        return 'ram'

    @classmethod
    def supported_platforms(cls):
        return ['macos', 'linux']


