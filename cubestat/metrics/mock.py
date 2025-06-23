from argparse import ArgumentParser

from cubestat.metrics.metric_adapter import MetricAdapter
from cubestat.metrics_registry import collector_registry, cubestat_metric, presenter_registry


class MockMetricAdapter(MetricAdapter):
    """Mock metric adapter for testing purposes."""

    @classmethod
    def key(cls) -> str:
        return "mock"

    @classmethod
    def configure_argparse(cls, parser: ArgumentParser) -> None:
        # Get presenter class to configure argparse
        presenter_cls = presenter_registry.get("mock")
        if presenter_cls:
            presenter_cls.configure_argparse(parser)


@cubestat_metric("darwin")
class mock_metric(MockMetricAdapter):
    """macOS mock metric using new collector/presenter architecture."""

    def __init__(self):
        collector = collector_registry.get_instance("darwin", "mock")
        presenter = presenter_registry.get_instance("mock")
        super().__init__(collector, presenter)


@cubestat_metric("linux")
class linux_mock_metric(MockMetricAdapter):
    """Linux mock metric using new collector/presenter architecture."""

    def __init__(self):
        collector = collector_registry.get_instance("linux", "mock")
        presenter = presenter_registry.get_instance("mock")
        super().__init__(collector, presenter)
