import psutil
import time

from cubestat.readers.mem_reader import MemReader
from cubestat.readers.nv_reader import NVReader
from cubestat.readers.swap import SwapLinuxReader
from cubestat.readers.cpu import CPULinuxReader

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

class LinuxReader:
    def __init__(self, interval_ms):
        self.first = True
        self.interval_ms = interval_ms
        self.mem_reader = MemReader(interval_ms)
        self.nv = NVReader()
        self.swap_reader = SwapLinuxReader()
        self.cpu_reader  = CPULinuxReader()
        self.rate_reader = RateReader(self.interval_ms)

    def read(self):
        res = self.mem_reader.read()
        res['swap'] = self.swap_reader.read()

        disk_load = psutil.disk_io_counters()
        nw_load = psutil.net_io_counters()

        res['cpu'], cpu_clusters = self.cpu_reader.read()
        res['gpu'] = self.nv.read()
        res['disk']['disk read']  = self.rate_reader.next('disk read', disk_load.read_bytes)
        res['disk']['disk write']  = self.rate_reader.next('disk write', disk_load.write_bytes)
        res['network']['network rx'] = self.rate_reader.next('network rx', nw_load.bytes_sent)
        res['network']['network tx'] = self.rate_reader.next('network tx', nw_load.bytes_recv)

        return res.items(), cpu_clusters

    def loop(self, on_snapshot_cb):
        # TODO: should this be monotonic?
        begin_ts = time.time()
        n = 0
        d = self.interval_ms / 1000.0
        while True:
            snapshot, cpu_clusters = self.read()
            on_snapshot_cb(snapshot, cpu_clusters)
            n += 1
            expected_time = begin_ts + n * d
            current_time = time.time()
            if expected_time > current_time:
                time.sleep(expected_time - current_time)
