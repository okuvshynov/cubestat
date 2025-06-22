from argparse import ArgumentParser
from typing import Any, Dict

from cubestat.metrics.metric_adapter import MetricAdapter
from cubestat.metrics_registry import collector_registry, cubestat_metric, presenter_registry


class MockMetricAdapter(MetricAdapter):
    """Mock metric adapter for testing purposes."""

    def read(self, context: Dict[str, Any]) -> Dict[str, float]:
        """Read mock data and convert to display format."""
        raw_data = self.collector.collect(context)
        return self.presenter.process_data(raw_data)

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


# Keep old implementation commented for reference
"""
from cubestat.metrics.base_metric import base_metric
from cubestat.metrics_registry import cubestat_metric

@cubestat_metric('darwin')
class mock_metric(base_metric):
    def read(self, context):
        res = {'mock': self.v}
        self.v += 1.0
        return res

    def pre(self, title):
        return False, ''
    
    def format(self, title, values, idxs):
        return 100.0, [f'{values[i]:3.0f}%' for i in idxs]

    @classmethod
    def key(cls):
        return 'mock'

    def hotkey(self):
        return 'w'

    @classmethod
    def configure_argparse(cls, parser):
        pass

    def configure(self, conf):
        self.v = 0.0
        return self
"""

