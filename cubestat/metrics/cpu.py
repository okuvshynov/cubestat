import psutil

from cubestat.common import CPUMode

# TODO: also need to define:
#  - options (command-line, hotkey)
#  - presentation of the values
#  - colors
class cpu_metric:
    def __init__(self, platform) -> None:
        if platform == 'linux':
            self.read = self.read_linux
        if platform == 'macos':
            self.read = self.read_osx

    def read_osx(self, context):
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
    
    def read_linux(self, _context):
        # TODO: numa nodes here?
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
    
    def pre(self, mode, title):
        if mode == CPUMode.by_cluster and title not in self.cpu_clusters:
            return False, ''
        if mode == CPUMode.by_core and title in self.cpu_clusters:
            return False, ''
        if mode == CPUMode.all and title not in self.cpu_clusters:
            return True, '  '
        else:
            return True, ''
    
    def rows(self, mode, data):
        res = []
        for title, series in data.items():
            if mode == CPUMode.by_cluster and title not in self.cpu_clusters:
                continue
            if mode == CPUMode.by_core and title in self.cpu_clusters:
                continue
            if mode == CPUMode.all and title not in self.cpu_clusters:
                res.append(('  ', title, series))
            else:
                res.append(('', title, series))
        return res