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

