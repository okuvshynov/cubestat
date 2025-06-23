from argparse import ArgumentParser
from typing import Any, Dict, List, Optional, Sequence, Tuple

from cubestat.common import SimpleMode
from cubestat.metrics_registry import presenter_registry
from cubestat.presenters.base_presenter import BasePresenter


@presenter_registry.register
class AccelPresenter(BasePresenter):
    """Accelerator (ANE) presenter handling display."""

    def __init__(self):
        self.mode = SimpleMode.show

    @classmethod
    def key(cls) -> str:
        return "accel"


    def configure(self, config) -> "AccelPresenter":
        # ANE metric doesn't have configurable modes, always shown
        # But maintain consistent interface
        self.mode = SimpleMode.show
        return self

    def pre(self, _title: str) -> Tuple[bool, str]:
        """ANE metrics are always shown without indentation."""
        return True, ""

    def format(
        self, _title: str, values: Sequence[float], idxs: Sequence[int]
    ) -> Tuple[float, List[str]]:
        """Format ANE utilization as percentages."""
        return 100.0, [f"{values[i]:3.0f}%" for i in idxs]

    def hotkey(self) -> Optional[str]:
        """ANE metric doesn't have a hotkey."""
        return None

    @classmethod
    def configure_argparse(cls, parser: ArgumentParser) -> None:
        """ANE metric doesn't have command-line arguments."""
        pass

    def process_data(self, raw_data: Dict[str, Any]) -> Dict[str, float]:
        """Convert collector data to display format."""
        result = {}

        # Handle standardized metric names from collector
        if "accel.ane.utilization.percent" in raw_data:
            result["ANE util %"] = raw_data["accel.ane.utilization.percent"]

        return result
