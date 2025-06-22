from argparse import ArgumentParser
from typing import Any, Dict, List, Optional, Sequence, Tuple

from cubestat.common import SimpleMode, label_bytes
from cubestat.metrics_registry import presenter_registry
from cubestat.presenters.base_presenter import BasePresenter


@presenter_registry.register
class SwapPresenter(BasePresenter):
    """Swap presenter handling swap display formatting."""

    def __init__(self):
        self.mode = SimpleMode.show

    @classmethod
    def key(cls) -> str:
        return "swap"

    @classmethod
    def collector_id(cls) -> str:
        return "swap"

    def configure(self, config) -> "SwapPresenter":
        """Configure swap display mode."""
        # Handle both Dict and Namespace objects
        if hasattr(config, "get"):
            mode_value = config.get("swap", SimpleMode.show)
        else:
            mode_value = getattr(config, "swap", SimpleMode.show)

        # Ensure we have a proper SimpleMode enum, not a string
        if isinstance(mode_value, str):
            self.mode = SimpleMode(mode_value)
        else:
            self.mode = mode_value
        return self

    def pre(self, title: str) -> Tuple[bool, str]:
        """Filter swap metrics based on display mode."""
        if self.mode == SimpleMode.hide:
            return False, ""
        return True, ""

    def format(
        self, title: str, values: Sequence[float], idxs: Sequence[int]
    ) -> Tuple[float, List[str]]:
        """Format swap values as byte labels."""
        return label_bytes(values, idxs)

    def hotkey(self) -> Optional[str]:
        """Return hotkey for swap metric."""
        return "s"

    @classmethod
    def configure_argparse(cls, parser: ArgumentParser) -> None:
        """Configure command-line arguments."""
        parser.add_argument(
            "--swap",
            type=SimpleMode,
            default=SimpleMode.show,
            choices=list(SimpleMode),
            help='swap show/hide. Hotkey: "s"',
        )

    def process_data(self, raw_data: Dict[str, Any]) -> Dict[str, float]:
        """Convert collector data to display format with proper titles."""
        result = {}

        # Map collector keys to display titles
        if "used_bytes" in raw_data:
            result["swap used"] = raw_data["used_bytes"]

        return result