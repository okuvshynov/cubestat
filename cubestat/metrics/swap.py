from argparse import ArgumentParser
from typing import Any, Dict

from cubestat.metrics.metric_adapter import MetricAdapter
from cubestat.metrics_registry import collector_registry, cubestat_metric, presenter_registry


class SwapMetricAdapter(MetricAdapter):
    """Swap metric adapter handling data processing."""

    def read(self, context: Dict[str, Any]) -> Dict[str, float]:
        """Read swap data and convert to display format."""
        raw_data = self.collector.collect(context)
        return self.presenter.process_data(raw_data)

    @classmethod
    def key(cls) -> str:
        return "swap"

    @classmethod
    def configure_argparse(cls, parser: ArgumentParser) -> None:
        # Get presenter class to configure argparse
        presenter_cls = presenter_registry.get("swap")
        if presenter_cls:
            presenter_cls.configure_argparse(parser)


@cubestat_metric("darwin")
class macos_swap_metric(SwapMetricAdapter):
    """macOS swap metric using new collector/presenter architecture."""

    def __init__(self):
        collector = collector_registry.get_instance("darwin", "swap")
        presenter = presenter_registry.get_instance("swap")
        super().__init__(collector, presenter)


@cubestat_metric("linux")
class linux_swap_metric(SwapMetricAdapter):
    """Linux swap metric using new collector/presenter architecture."""

    def __init__(self):
        collector = collector_registry.get_instance("linux", "swap")
        presenter = presenter_registry.get_instance("swap")
        super().__init__(collector, presenter)

