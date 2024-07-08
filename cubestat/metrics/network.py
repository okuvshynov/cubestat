import psutil

from cubestat.common import SimpleMode, RateReader, label2
from cubestat.metrics.base_metric import base_metric
from cubestat.metrics.registry import register_metric

class network_metric(base_metric):
    def pre(self, mode, title):
        if mode == SimpleMode.hide:
            return False, ''
        return True, ''
    
    def format(self, values, idxs):
        return label2(values, [(1024 * 1024, 'MB/s'), (1024, 'KB/s'), (1, 'Bytes/s')], idxs)

    @classmethod
    def key(cls):
        return 'network'

    def configure(self, conf):
        self.rate_reader = RateReader(conf['interval_ms'])
        return self

@register_metric
class macos_network_metric(network_metric):
    def read(self, context):
        res = {}
        res['network rx'] = context['network']['ibyte_rate']
        res['network tx'] = context['network']['obyte_rate']
        return res

    @classmethod
    def supported_platforms(cls):
        return ['macos']

    
@register_metric
class linux_network_metric(network_metric):
    def read(self, _context):
        res = {}
        net_io = psutil.net_io_counters()
        res['network rx'] = self.rate_reader.next('network rx', net_io.bytes_sent)
        res['network tx'] = self.rate_reader.next('network tx', net_io.bytes_recv)
        return res
    
    @classmethod
    def supported_platforms(cls):
        return ['linux']
