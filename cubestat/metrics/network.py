from argparse import ArgumentParser
from typing import Any, Dict

from cubestat.metrics.metric_adapter import MetricAdapter
from cubestat.metrics_registry import collector_registry, cubestat_metric, presenter_registry


class NetworkMetricAdapter(MetricAdapter):
    """Network metric adapter handling data processing."""

    def read(self, context: Dict[str, Any]) -> Dict[str, float]:
        """Read network data and convert to display format."""
        raw_data = self.collector.collect(context)
        return self.presenter.process_data(raw_data)

    def configure(self, config) -> "NetworkMetricAdapter":
        """Configure both collector and presenter."""
        self.collector.configure(config)
        self.presenter.configure(config)
        return self

    @classmethod
    def key(cls) -> str:
        return "network"

    @classmethod
    def configure_argparse(cls, parser: ArgumentParser) -> None:
        # Get presenter class to configure argparse
        presenter_cls = presenter_registry.get("network")
        if presenter_cls:
            presenter_cls.configure_argparse(parser)


@cubestat_metric("darwin")
class macos_network_metric(NetworkMetricAdapter):
    """macOS network metric using new collector/presenter architecture."""

    def __init__(self):
        collector = collector_registry.get_instance("darwin", "network")
        presenter = presenter_registry.get_instance("network")
        super().__init__(collector, presenter)


@cubestat_metric("linux")
class linux_network_metric(NetworkMetricAdapter):
    """Linux network metric using new collector/presenter architecture."""

    def __init__(self):
        collector = collector_registry.get_instance("linux", "network")
        presenter = presenter_registry.get_instance("network")
        super().__init__(collector, presenter)


# Keep old implementation commented for reference
"""
import psutil

from cubestat.common import SimpleMode, RateReader, label_bytes_per_sec
from cubestat.metrics.base_metric import base_metric
from cubestat.metrics_registry import cubestat_metric


class network_metric(base_metric):
    def pre(self, title):
        if self.mode == SimpleMode.hide:
            return False, ''
        return True, ''

    def format(self, title, values, idxs):
        return label_bytes_per_sec(values, idxs)

    @classmethod
    def key(cls):
        return 'network'

    def hotkey(self):
        return 'n'

    def configure(self, conf):
        self.mode = conf.network
        self.rate_reader = RateReader(conf.refresh_ms)
        return self

    @classmethod
    def configure_argparse(cls, parser):
        parser.add_argument(
            '--network',
            type=SimpleMode,
            default=SimpleMode.show,
            choices=list(SimpleMode),
            help='Show network io. Hotkey: "n"'
        )


@cubestat_metric('darwin')
class macos_network_metric(network_metric):
    def read(self, context):
        res = {}
        res['network rx'] = context['network']['ibyte_rate']
        res['network tx'] = context['network']['obyte_rate']
        return res


@cubestat_metric('linux')
class linux_network_metric(network_metric):
    def read(self, _context):
        res = {}
        net_io = psutil.net_io_counters()
        res['network rx'] = self.rate_reader.next('network rx', net_io.bytes_sent)
        res['network tx'] = self.rate_reader.next('network tx', net_io.bytes_recv)
        return res
"""
