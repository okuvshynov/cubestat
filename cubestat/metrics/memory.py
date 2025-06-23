from argparse import ArgumentParser

from cubestat.metrics.metric_adapter import MetricAdapter
from cubestat.metrics_registry import collector_registry, cubestat_metric, presenter_registry


class MemoryMetricAdapter(MetricAdapter):
    """Memory metric adapter handling data processing."""

    @classmethod
    def key(cls) -> str:
        return "ram"

    @classmethod
    def configure_argparse(cls, parser: ArgumentParser) -> None:
        # Get presenter class to configure argparse
        presenter_cls = presenter_registry.get("memory")
        if presenter_cls:
            presenter_cls.configure_argparse(parser)


@cubestat_metric("darwin")
class ram_metric_macos(MemoryMetricAdapter):
    """macOS memory metric using new collector/presenter architecture."""

    def __init__(self):
        collector = collector_registry.get_instance("darwin", "memory")
        presenter = presenter_registry.get_instance("memory")
        super().__init__(collector, presenter)


@cubestat_metric("linux")
class ram_metric_linux(MemoryMetricAdapter):
    """Linux memory metric using new collector/presenter architecture."""

    def __init__(self):
        collector = collector_registry.get_instance("linux", "memory")
        presenter = presenter_registry.get_instance("memory")
        super().__init__(collector, presenter)
