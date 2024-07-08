import psutil

from cubestat.common import SimpleMode, RateReader, label2
from cubestat.metrics.base_metric import base_metric
from cubestat.metrics.registry import register_metric

class disk_metric(base_metric):
    def pre(self, mode, title):
        if mode == SimpleMode.hide:
            return False, ''
        return True, ''
    
    def format(self, values, idxs):
        return label2(values, [(1024 * 1024, 'MB/s'), (1024, 'KB/s'), (1, 'Bytes/s')], idxs)

    @classmethod
    def key(cls):
        return 'disk'

    def configure(self, conf):
        self.rate_reader = RateReader(conf['interval_ms'])
        return self


@register_metric
class macos_disc_metric(disk_metric):
    def read(self, context):
        res = {}
        res['disk read']  = context['disk']['rbytes_per_s']
        res['disk write'] = context['disk']['wbytes_per_s']
        return res

    @classmethod
    def supported_platforms(cls):
        return ['macos']
    
@register_metric
class linux_disc_metric(disk_metric):
    def read(self, _context):
        res = {}
        disk_io = psutil.disk_io_counters()
        res['disk read']  = self.rate_reader.next('disk read', disk_io.read_bytes)
        res['disk write']  = self.rate_reader.next('disk write', disk_io.write_bytes)
        return res
    
    @classmethod
    def supported_platforms(cls):
        return ['linux']
