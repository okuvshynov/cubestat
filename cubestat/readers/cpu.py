import psutil

class CPUMacOSReader:
    def __init__(self):
        pass

    def read(self, snapshot):
        cpu_clusters = []
        res = {}
        for cluster in snapshot['processor']['clusters']:
            idle_cluster, total_cluster = 0.0, 0.0
            n_cpus = len(cluster['cpus'])
            cluster_title = f'[{n_cpus}] {cluster["name"]} total CPU util %'
            cpu_clusters.append(cluster_title)
            res[cluster_title] = 0.0
            for cpu in cluster['cpus']:
                title = f'{cluster["name"]} CPU {cpu["cpu"]} util %'
                res[title] = 100.0 - 100.0 * cpu['idle_ratio']
                idle_cluster += cpu['idle_ratio']
                total_cluster += 1.0
            res[cluster_title] = 100.0 - 100.0 * idle_cluster / total_cluster

        return res, cpu_clusters

class CPULinuxReader:
    def __init__(self) -> None:
        pass

    def read(self):
        # TODO: numa nodes here?
        cpu_clusters = []
        cpu_load = psutil.cpu_percent(percpu=True)
        res = {}
        
        cluster_title = f'[{len(cpu_load)}] Total CPU Util, %'
        cpu_clusters.append(cluster_title)
        total_load = 0.0
        res[cluster_title] = 0.0

        for i, v in enumerate(cpu_load):
            title = f'CPU {i} util %'
            res[title] = v
            total_load += v
        res[cluster_title] = total_load / len(cpu_load)

        return res, cpu_clusters