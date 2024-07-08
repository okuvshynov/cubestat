import psutil

from cubestat.metrics.base_metric import base_metric
from cubestat.metrics.registry import cubestat_metric

@cubestat_metric('darwin', 'linux')
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

"""
@cubestat_metric('darwin', 'linux')
class abs_ram_metric(base_metric):
    def read(self, _context):
        return {'RAM used': psutil.virtual_memory().used}
    
    def pre(self, mode, title):
        return True, ''
    
    def format(self, values, idxs):
        return label2(values, [(1024 ** 3, 'GB'), (1024 ** 2, 'MB'), (1024, 'KB'), (1, 'Bytes')], idxs)

    @classmethod
    def key(cls):
        return 'ram_abs'
"""
