from argparse import ArgumentParser
from typing import Any, Dict

from cubestat.metrics.metric_adapter import MetricAdapter
from cubestat.metrics_registry import collector_registry, cubestat_metric, presenter_registry


class GPUMetricAdapter(MetricAdapter):
    """GPU metric adapter handling multi-vendor GPU data processing."""

    def read(self, context: Dict[str, Any]) -> Dict[str, float]:
        """Read GPU data and convert to display format."""
        raw_data = self.collector.collect(context)
        return self.presenter.process_data(raw_data)

    @classmethod
    def key(cls) -> str:
        return "gpu"

    @classmethod
    def configure_argparse(cls, parser: ArgumentParser) -> None:
        # Get presenter class to configure argparse
        presenter_cls = presenter_registry.get("gpu")
        if presenter_cls:
            presenter_cls.configure_argparse(parser)




@cubestat_metric("linux")
class unified_gpu_metric_linux(GPUMetricAdapter):
    """Linux GPU metric using new collector/presenter architecture."""

    def __init__(self):
        collector = collector_registry.get_instance("linux", "gpu")
        presenter = presenter_registry.get_instance("gpu")
        super().__init__(collector, presenter)


@cubestat_metric("darwin")
class unified_gpu_metric_macos(GPUMetricAdapter):
    """macOS GPU metric using new collector/presenter architecture."""

    def __init__(self):
        collector = collector_registry.get_instance("darwin", "gpu")
        presenter = presenter_registry.get_instance("gpu")
        super().__init__(collector, presenter)
