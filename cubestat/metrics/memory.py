import psutil

from cubestat.metrics.base_metric import base_metric
from cubestat.metrics.registry import cubestat_metric
from cubestat.common import label2
from cubestat.common import DisplayMode

class RAMMode(DisplayMode):
    percent = 'percent'
    all  = 'all'

@cubestat_metric('linux')
class ram_metric(base_metric):
    def read(self, _context):
        return {'RAM used %': psutil.virtual_memory().percent}
    
    def pre(self, title):
        return True, ''
    
    def format(self, title, values, idxs):
        return 100.0, [f'{values[i]:3.0f}%' for i in idxs]

    @classmethod
    def key(cls):
        return 'ram'

@cubestat_metric('darwin')
class ram_metric_ex(base_metric):
    def read(self, _context):
        vm = psutil.virtual_memory()
        return {
            'RAM used %' : vm.percent,
            'RAM used'   : vm.used,
            'RAM wired'  : vm.wired,
        }

    def configure(self, _conf):
        self.mode = RAMMode.all
        return self

    def hotkey(self):
        return 'm'
    
    def pre(self, title):
        if title == 'RAM used %':
            return True, ''
        if self.mode == RAMMode.all:
            return True, '  '
        return False, ''
    
    def format(self, title, values, idxs):
        if title == 'RAM used %':
            return 100.0, [f'{values[i]:3.0f}%' for i in idxs]
        return label2(values, [(1024 ** 3, 'GB'), (1024 ** 2, 'MB'), (1024, 'KB'), (1, 'Bytes')], idxs)

    @classmethod
    def key(cls):
        return 'ram_abs'
