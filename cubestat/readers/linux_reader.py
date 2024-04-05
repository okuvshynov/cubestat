import psutil
import time

from cubestat.readers.mem_reader import MemReader
from cubestat.readers.nv_reader import NVReader
from cubestat.readers.free_swap_reader import FreeSwapReader

class LinuxReader:
    def __init__(self, interval_ms):
        self.first = True
        self.interval_ms = interval_ms
        self.mem_reader = MemReader(interval_ms)
        self.nv = NVReader()
        self.swap_reader = FreeSwapReader()

    def read(self):
        res = self.mem_reader.read()
        res['swap'] = self.swap_reader.read()

        disk_load = psutil.disk_io_counters()
        nw_load = psutil.net_io_counters()
        d = self.interval_ms / 1000.0

        # TODO: numa nodes here?
        cpu_clusters = []
        cpu_load = psutil.cpu_percent(percpu=True)

        cluster_title = f'[{len(cpu_load)}] Total CPU Util, %'
        cpu_clusters.append(cluster_title)
        total_load = 0.0
        res['cpu'][cluster_title] = 0.0

        for i, v in enumerate(cpu_load):
            title = f'CPU {i} util %'
            res['cpu'][title] = v
            total_load += v
        res['cpu'][cluster_title] = total_load / len(cpu_load)

        res['gpu'] = self.nv.read()

        if self.first:
            self.disk_read_last = disk_load.read_bytes
            self.disk_written_last = disk_load.write_bytes
            self.network_read_last = nw_load.bytes_recv
            self.network_written_last = nw_load.bytes_sent
            self.first = False

        res['disk']['disk read'] = ((disk_load.read_bytes - self.disk_read_last) / d)
        res['disk']['disk write'] = ((disk_load.write_bytes - self.disk_written_last) / d)
        self.disk_read_last = disk_load.read_bytes
        self.disk_written_last = disk_load.write_bytes

        res['network']['network rx'] = ((nw_load.bytes_recv - self.network_read_last) / d)
        res['network']['network tx'] = ((nw_load.bytes_sent - self.network_written_last) / d)
        self.network_read_last = nw_load.bytes_recv
        self.network_written_last = nw_load.bytes_sent

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
