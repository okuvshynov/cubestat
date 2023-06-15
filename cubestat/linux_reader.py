import psutil
import subprocess
from importlib.util import find_spec

class LinuxReader:
    def __init__(self, interval_ms):
        self.has_nvidia = False
        self.first = True
        self.interval_ms = interval_ms
        try:
            subprocess.check_output('nvidia-smi')
            nvspec = find_spec('pynvml')
            if nvspec is not None:
                from pynvml.smi import nvidia_smi
                self.nvsmi = nvidia_smi.getInstance()
                self.has_nvidia = True
        except Exception:
            # TODO: add logging here
            pass

    def read(self):
        res = {
            'cpu': {},
            'accelerators': {},
            'ram': {'RAM used %': psutil.virtual_memory().percent},
            'disk': {},
            'network': {},
        }

        disk_load = psutil.disk_io_counters()
        disk_read_kb = disk_load.read_bytes / 2 ** 10
        disk_written_kb = disk_load.write_bytes / 2 ** 10
        nw_load = psutil.net_io_counters()
        nw_read_kb = nw_load.bytes_recv / 2 ** 10
        nw_written_kb = nw_load.bytes_sent / 2 ** 10
        d = self.interval_ms / 1000.0

        cpu_clusters = []

        cluster_title = 'Total CPU util %'
        cpu_clusters.append(cluster_title)
        total_load = 0.0
        res['cpu'][cluster_title] = 0.0

        cpu_load = psutil.cpu_percent(percpu=True)
        for i, v in enumerate(cpu_load):
            title = f'CPU {i} util %'
            res['cpu'][title] = v
            total_load += v
        res['cpu'][cluster_title] = total_load / len(cpu_load)

        if self.has_nvidia:
            for i, v in enumerate(self.nvsmi.DeviceQuery('utilization.gpu')['gpu']):
                title = f'GPU {i} util %'
                res['accelerators'][title] = v['utilization']['gpu_util']

        if self.first:
            self.disk_read_last = disk_read_kb
            self.disk_written_last = disk_written_kb
            self.network_read_last = nw_read_kb
            self.network_written_last = nw_written_kb
            self.first = False

        res['disk']['disk read KB/s'] = ((disk_read_kb - self.disk_read_last) / d)
        res['disk']['disk write KB/s'] = ((disk_written_kb - self.disk_written_last) / d)
        self.disk_read_last = disk_read_kb
        self.disk_written_last = disk_written_kb

        res['network']['network i KB/s'] = ((nw_read_kb - self.network_read_last) / d)
        res['network']['network w KB/s'] = ((nw_written_kb - self.network_written_last) / d)
        self.network_read_last = nw_read_kb
        self.network_written_last = nw_written_kb

        return res.items(), cpu_clusters