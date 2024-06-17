import time

from cubestat.readers.mem_reader import MemReader
from cubestat.readers.nv_reader import NVReader

from cubestat.common import RateReader

class LinuxReader:
    def __init__(self, interval_ms):
        self.first = True
        self.interval_ms = interval_ms
        self.mem_reader = MemReader(interval_ms)
        self.nv = NVReader()
        self.rate_reader = RateReader(self.interval_ms)
        self.platform    = 'linux'

    def read(self):
        res = self.mem_reader.read()
        res['gpu'] = self.nv.read()
        return res.items()

    def loop(self, on_snapshot_cb):
        # TODO: should this be monotonic?
        begin_ts = time.time()
        n = 0
        d = self.interval_ms / 1000.0
        while True:
            snapshot = self.read()
            on_snapshot_cb(snapshot, None)
            n += 1
            expected_time = begin_ts + n * d
            current_time = time.time()
            if expected_time > current_time:
                time.sleep(expected_time - current_time)
