import psutil

from cubestat.metrics.base_metric import base_metric
from cubestat.metrics.registry import cubestat_metric
from cubestat.common import CPUMode

class cpu_metric(base_metric):
    def pre(self, mode, title):
        if mode == CPUMode.by_cluster and title not in self.cpu_clusters:
            return False, ''
        if mode == CPUMode.by_core and title in self.cpu_clusters:
            return False, ''
        if mode == CPUMode.all and title not in self.cpu_clusters:
            return True, '  '
        else:
            return True, ''

    def format(self, values, idxs):
        return 100.0, [f'{values[i]:3.0f}%' for i in idxs]

    @classmethod
    def key(cls):
        return 'cpu'

@cubestat_metric('linux')
class psutil_cpu_metric(cpu_metric):
    def read(self, _context):
        self.cpu_clusters = []
        cpu_load = psutil.cpu_percent(percpu=True)
        res = {}
        
        cluster_title = f'[{len(cpu_load)}] Total CPU Util, %'
        self.cpu_clusters.append(cluster_title)
        total_load = 0.0
        res[cluster_title] = 0.0

        for i, v in enumerate(cpu_load):
            title = f'CPU {i} util %'
            res[title] = v
            total_load += v
        res[cluster_title] = total_load / len(cpu_load)

        return res

@cubestat_metric('macos')
class macos_cpu_metric(cpu_metric):
    def read(self, context):
        self.cpu_clusters = []
        res = {}
        for cluster in context['processor']['clusters']:
            idle_cluster, total_cluster = 0.0, 0.0
            n_cpus = len(cluster['cpus'])
            cluster_title = f'[{n_cpus}] {cluster["name"]} total CPU util %'
            self.cpu_clusters.append(cluster_title)
            res[cluster_title] = 0.0
            for cpu in cluster['cpus']:
                title = f'{cluster["name"]} CPU {cpu["cpu"]} util %'
                res[title] = 100.0 - 100.0 * cpu['idle_ratio']
                idle_cluster += cpu['idle_ratio']
                total_cluster += 1.0
            res[cluster_title] = 100.0 - 100.0 * idle_cluster / total_cluster

        return res

