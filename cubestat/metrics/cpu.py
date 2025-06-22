from argparse import ArgumentParser
from typing import Any, Dict

from cubestat.metrics.metric_adapter import MetricAdapter
from cubestat.metrics_registry import collector_registry, cubestat_metric, presenter_registry


class CPUMetricAdapter(MetricAdapter):
    """CPU metric adapter handling hierarchical data."""

    def read(self, context: Dict[str, Any]) -> Dict[str, float]:
        """Read hierarchical CPU data and convert to display format."""
        raw_data = self.collector.collect(context)

        # Convert collector data to display format
        self.presenter.cpu_clusters = []
        result = {}

        for cluster in raw_data["clusters"]:
            # Add cluster total
            cluster_title = f"[{len(cluster.cpus)}] {cluster.name} total CPU util %"
            self.presenter.cpu_clusters.append(cluster_title)
            result[cluster_title] = cluster.total_utilization

            # Add individual CPUs
            for cpu in cluster.cpus:
                cpu_title = f"{cluster.name} CPU {cpu['cpu']} util %"
                result[cpu_title] = cpu["utilization"]

        return result

    @classmethod
    def key(cls) -> str:
        return "cpu"

    @classmethod
    def configure_argparse(cls, parser: ArgumentParser) -> None:
        # Get presenter class to configure argparse
        presenter_cls = presenter_registry.get("cpu")
        if presenter_cls:
            presenter_cls.configure_argparse(parser)


@cubestat_metric("linux")
class psutil_cpu_metric(CPUMetricAdapter):
    """Linux CPU metric using new collector/presenter architecture."""

    def __init__(self):
        collector = collector_registry.get_instance("linux", "cpu")
        presenter = presenter_registry.get_instance("cpu")
        super().__init__(collector, presenter)


@cubestat_metric("darwin")
class macos_cpu_metric(CPUMetricAdapter):
    """macOS CPU metric using new collector/presenter architecture."""

    def __init__(self):
        collector = collector_registry.get_instance("darwin", "cpu")
        presenter = presenter_registry.get_instance("cpu")
        super().__init__(collector, presenter)


# Keep old implementation commented for reference
"""
import os
import psutil

from cubestat.metrics.base_metric import base_metric
from cubestat.metrics_registry import cubestat_metric
from cubestat.common import DisplayMode


class CPUMode(DisplayMode):
    all = 'all'
    by_cluster = 'by_cluster'
    by_core = 'by_core'


def auto_cpu_mode() -> CPUMode:
    return CPUMode.all if os.cpu_count() < 20 else CPUMode.by_cluster


class cpu_metric(base_metric):
    def pre(self, title):
        if self.mode == CPUMode.by_cluster and title not in self.cpu_clusters:
            return False, ''
        if self.mode == CPUMode.by_core and title in self.cpu_clusters:
            return False, ''
        if self.mode == CPUMode.all and title not in self.cpu_clusters:
            return True, '  '
        else:
            return True, ''

    def format(self, title, values, idxs):
        return 100.0, [f'{values[i]:3.0f}%' for i in idxs]

    def configure(self, conf):
        self.mode = conf.cpu
        return self

    @classmethod
    def key(cls):
        return 'cpu'

    def hotkey(self):
        return 'c'

    @classmethod
    def configure_argparse(cls, parser):
        parser.add_argument(
            '--cpu',
            type=CPUMode,
            default=auto_cpu_mode(),
            choices=list(CPUMode),
            help='Select CPU mode: all cores, cumulative by cluster, or both. Hotkey: "c".'
        )


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


@cubestat_metric('darwin')
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
"""
