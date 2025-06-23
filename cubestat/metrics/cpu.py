from argparse import ArgumentParser

from cubestat.metrics.metric_adapter import MetricAdapter
from cubestat.metrics_registry import collector_registry, cubestat_metric, presenter_registry


class CPUMetricAdapter(MetricAdapter):
    """CPU metric adapter handling hierarchical data."""

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

