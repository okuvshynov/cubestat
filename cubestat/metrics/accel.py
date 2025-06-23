from argparse import ArgumentParser

from cubestat.metrics.metric_adapter import MetricAdapter
from cubestat.metrics_registry import collector_registry, cubestat_metric, presenter_registry


class AccelMetricAdapter(MetricAdapter):
    """Accelerator (ANE) metric adapter handling data processing."""

    @classmethod
    def key(cls) -> str:
        return "ane"

    @classmethod
    def configure_argparse(cls, _parser: ArgumentParser) -> None:
        # ANE metric doesn't have command-line arguments
        pass


@cubestat_metric("darwin")
class ane_metric(AccelMetricAdapter):
    """macOS ANE metric using new collector/presenter architecture."""

    def __init__(self):
        collector = collector_registry.get_instance("darwin", "accel")
        presenter = presenter_registry.get_instance("accel")
        super().__init__(collector, presenter)


# Linux ANE metric not applicable - ANE (Apple Neural Engine) is Apple Silicon specific
# No equivalent accelerator hardware with standard APIs on Linux systems
