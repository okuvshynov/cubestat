from argparse import ArgumentParser
from typing import Any, Dict

from cubestat.metrics.metric_adapter import MetricAdapter
from cubestat.metrics_registry import collector_registry, cubestat_metric, presenter_registry


class PowerMetricAdapter(MetricAdapter):
    """Power metric adapter handling data processing."""

    def read(self, context: Dict[str, Any]) -> Dict[str, float]:
        """Read power data and convert to display format."""
        raw_data = self.collector.collect(context)
        return self.presenter.process_data(raw_data)

    @classmethod
    def key(cls) -> str:
        return "power"

    @classmethod
    def configure_argparse(cls, parser: ArgumentParser) -> None:
        # Get presenter class to configure argparse
        presenter_cls = presenter_registry.get("power")
        if presenter_cls:
            presenter_cls.configure_argparse(parser)


@cubestat_metric("darwin")
class macos_power_metric(PowerMetricAdapter):
    """macOS power metric using new collector/presenter architecture."""

    def __init__(self):
        collector = collector_registry.get_instance("darwin", "power")
        presenter = presenter_registry.get_instance("power")
        super().__init__(collector, presenter)


# Linux power metric disabled - power data not available on Linux systems
# @cubestat_metric("linux")
# class linux_power_metric(PowerMetricAdapter):
#     """Linux power metric using new collector/presenter architecture."""
# 
#     def __init__(self):
#         collector = collector_registry.get_instance("linux", "power")
#         presenter = presenter_registry.get_instance("power")
#         super().__init__(collector, presenter)

