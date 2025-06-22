from typing import Any, Dict

from cubestat.collectors.base_collector import BaseCollector
from cubestat.metrics_registry import collector_registry


class MockCollector(BaseCollector):
    """Base mock collector for testing purposes."""

    @classmethod
    def collector_id(cls) -> str:
        return "mock"


@collector_registry.register("darwin")
class MacOSMockCollector(MockCollector):
    """macOS mock collector that generates incrementing test data."""

    def __init__(self):
        self.counter = 0.0

    def collect(self, context: Dict[str, Any]) -> Dict[str, float]:
        """Generate mock data with incrementing counter."""
        value = self.counter
        self.counter += 1.0
        return {"mock_value": value}


@collector_registry.register("linux")
class LinuxMockCollector(MockCollector):
    """Linux mock collector that generates incrementing test data."""

    def __init__(self):
        self.counter = 0.0

    def collect(self, context: Dict[str, Any]) -> Dict[str, float]:
        """Generate mock data with incrementing counter."""
        value = self.counter
        self.counter += 1.0
        return {"mock_value": value}