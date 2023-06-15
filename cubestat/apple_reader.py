import psutil

class AppleReader:
    def __init__(self, interval_ms) -> None:
        self.interval_ms = interval_ms
        pass

    def read(self, snapshot):
        res = {
            'cpu': {},
            'accelerators': {},
            'ram': {'RAM used %': psutil.virtual_memory().percent},
            'disk': {},
            'network': {},
        }
        cpu_clusters = []
        for cluster in snapshot['processor']['clusters']:
            idle_cluster, total_cluster = 0.0, 0.0
            cluster_title = f'{cluster["name"]} total CPU util %'
            cpu_clusters.append(cluster_title)
            res['cpu'][cluster_title] = 0.0
            for cpu in cluster['cpus']:
                title = f'{cluster["name"]} CPU {cpu["cpu"]} util %'
                res['cpu'][title] = 100.0 - 100.0 * cpu['idle_ratio']
                idle_cluster += cpu['idle_ratio']
                total_cluster += 1.0
            res['cpu'][cluster_title] = 100.0 - 100.0 * idle_cluster / total_cluster

        res['accelerators']['GPU util %'] = 100.0 - 100.0 * snapshot['gpu']['idle_ratio']
        ane_scaling = 8.0 * self.interval_ms
        res['accelerators']['ANE util %'] = 100.0 * snapshot['processor']['ane_energy'] / ane_scaling

        res['disk']['disk read KB/s'] = snapshot['disk']['rbytes_per_s'] / (2 ** 10)
        res['disk']['disk write KB/s'] = snapshot['disk']['wbytes_per_s'] / (2 ** 10)
        res['network']['network i KB/s'] = snapshot['network']['ibyte_rate'] / (2 ** 10)
        res['network']['network o KB/s'] = snapshot['network']['obyte_rate'] / (2 ** 10)
        return res.items(), cpu_clusters

