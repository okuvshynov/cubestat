import psutil

from cubestat.common import SimpleMode, RateReader, label2

class disk_metric:
    def __init__(self, platform, interval_ms) -> None:
        if platform == 'linux':
            self.read = self.read_linux
        if platform == 'macos':
            self.read = self.read_macos
        self.rate_reader = RateReader(interval_ms)

    def read_macos(self, context):
        res = {}
        res['disk read']  = context['disk']['rbytes_per_s']
        res['disk write'] = context['disk']['wbytes_per_s']
        return res
    
    def read_linux(self, _context):
        res = {}
        disk_load = psutil.disk_io_counters()
        res['disk read']  = self.rate_reader.next('disk read', disk_load.read_bytes)
        res['disk write']  = self.rate_reader.next('disk write', disk_load.write_bytes)
        return res
    
    def pre(self, mode, title):
        if mode == SimpleMode.hide:
            return False, ''
        return True, ''
    
    def format(self, values, idxs):
        return label2(values, [(1024 * 1024, 'MB/s'), (1024, 'KB/s'), (1, 'Bytes/s')], idxs)