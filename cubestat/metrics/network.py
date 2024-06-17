import psutil

from cubestat.common import SimpleMode, RateReader

class network_metric:
    def __init__(self, platform, interval_ms) -> None:
        if platform == 'linux':
            self.read = self.read_linux
        if platform == 'macos':
            self.read = self.read_macos
        self.rate_reader = RateReader(interval_ms)

    def read_macos(self, context):
        res = {}
        res['network rx'] = context['network']['ibyte_rate']
        res['network tx'] = context['network']['obyte_rate']
        return res
    
    def read_linux(self, _context):
        res = {}
        nw_load = psutil.net_io_counters()
        res['network rx'] = self.rate_reader.next('network rx', nw_load.bytes_sent)
        res['network tx'] = self.rate_reader.next('network tx', nw_load.bytes_recv)
        return res
    
    def pre(self, mode, title):
        if mode == SimpleMode.hide:
            return False, ''
        return True, ''