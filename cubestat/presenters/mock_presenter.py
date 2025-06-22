from argparse import ArgumentParser
from typing import Any, Dict, List, Optional, Sequence, Tuple

from cubestat.metrics_registry import presenter_registry
from cubestat.presenters.base_presenter import BasePresenter


@presenter_registry.register
class MockPresenter(BasePresenter):
    """Mock presenter for test metric - always hidden with percentage formatting."""

    @classmethod
    def key(cls) -> str:
        return "mock"

    @classmethod
    def collector_id(cls) -> str:
        return "mock"

    def pre(self, title: str) -> Tuple[bool, str]:
        """Mock metric is always hidden (for testing only)."""
        return False, ""

    def format(
        self, title: str, values: Sequence[float], idxs: Sequence[int]
    ) -> Tuple[float, List[str]]:
        """Format mock values as percentages."""
        return 100.0, [f"{values[i]:3.0f}%" for i in idxs]

    def hotkey(self) -> Optional[str]:
        """Return hotkey for mock metric."""
        return "w"

    @classmethod
    def configure_argparse(cls, parser: ArgumentParser) -> None:
        """Mock metric has no configuration options."""
        pass

    def process_data(self, raw_data: Dict[str, Any]) -> Dict[str, float]:
        """Convert collector data to display format with proper titles."""
        result = {}

        # Map collector keys to display titles
        if "mock_value" in raw_data:
            result["mock"] = raw_data["mock_value"]

        return result