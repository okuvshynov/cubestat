import psutil

from cubestat.metrics.base_metric import base_metric
from cubestat.metrics_registry import cubestat_metric
from cubestat.common import label_bytes
from cubestat.common import DisplayMode


class RAMMode(DisplayMode):
    percent = 'percent'
    all = 'all'


class ram_metric(base_metric):
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
        return label_bytes(values, idxs)

    @classmethod
    def key(cls):
        return 'ram'


@cubestat_metric('darwin')
class ram_metric_macos(ram_metric):
    def read(self, _context):
        vm = psutil.virtual_memory()
        return {
            'RAM used %': vm.percent,
            'RAM used': vm.used,
            'RAM wired': vm.wired,
        }


@cubestat_metric('linux')
class ram_metric_linux(ram_metric):
    def __init__(self):
        # how to get metric from meminfo data
        self.rows = {
            'RAM used %': lambda mi: 100.0 * (mi['MemTotal'] - mi['MemAvailable']) / mi['MemTotal'],
            'RAM used': lambda mi: mi['MemTotal'] - mi['MemAvailable'],
            'RAM mapped': lambda mi: mi['Mapped'],
        }

    def read(self, _context):
        meminfo = {}
        with open('/proc/meminfo', 'r') as f:
            for line in f:
                key, value = line.split(':', 1)
                meminfo[key.strip()] = int(value.split()[0]) * 1024
        return {k: fn(meminfo) for k, fn in self.rows.items()}
