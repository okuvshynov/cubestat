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
        self.mode = getattr(config, "ane", SimpleMode.show)
        return self

    def pre(self, _title: str) -> Tuple[bool, str]:
        """Return visibility and indentation for ANE metrics."""
        if self.mode == SimpleMode.hide:
            return False, ""
        return True, ""

    def format(
        self, _title: str, values: Sequence[float], idxs: Sequence[int]
    ) -> Tuple[float, List[str]]:
        """Format ANE utilization as percentages."""
        return 100.0, [f"{values[i]:3.0f}%" for i in idxs]

    def hotkey(self) -> Optional[str]:
        """Return the hotkey for toggling ANE visibility."""
        return 'a'

    @classmethod
    def configure_argparse(cls, parser: ArgumentParser) -> None:
        parser.add_argument(
            "--ane",
            type=SimpleMode,
            default=SimpleMode.show,
            choices=list(SimpleMode),
            help='Show Apple Neural Engine utilization. Hotkey: "a"',
        )

    def process_data(self, raw_data: Dict[str, Any]) -> Dict[str, float]:
        """Convert collector data to display format."""
        result = {}

        # Handle standardized metric names from collector
        if "accel.ane.utilization.percent" in raw_data:
            result["ANE util %"] = raw_data["accel.ane.utilization.percent"]

        return result

    def toggle_visibility(self) -> None:
        """Toggle the visibility of the ANE metric."""
        self.visible = not self.visible
