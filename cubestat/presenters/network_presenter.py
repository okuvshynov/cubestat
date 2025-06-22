from argparse import ArgumentParser
from typing import Any, Dict, List, Optional, Sequence, Tuple

from cubestat.common import SimpleMode, label_bytes_per_sec
from cubestat.metrics_registry import presenter_registry
from cubestat.presenters.base_presenter import BasePresenter


@presenter_registry.register
class NetworkPresenter(BasePresenter):
    """Network presenter handling network I/O display."""

    def __init__(self):
        self.mode = SimpleMode.show

    @classmethod
    def key(cls) -> str:
        return "network"

    @classmethod
    def collector_id(cls) -> str:
        return "network"

    def configure(self, config) -> "NetworkPresenter":
        # Handle both Dict and Namespace objects
        if hasattr(config, "get"):
            mode_value = config.get("network", SimpleMode.show)
        else:
            mode_value = getattr(config, "network", SimpleMode.show)

        # Ensure we have a proper SimpleMode enum, not a string
        if isinstance(mode_value, str):
            self.mode = SimpleMode(mode_value)
        else:
            self.mode = mode_value
        return self

    def pre(self, _title: str) -> Tuple[bool, str]:
        """Filter network metrics based on display mode."""
        if self.mode == SimpleMode.hide:
            return False, ""
        return True, ""

    def format(
        self, _title: str, values: Sequence[float], idxs: Sequence[int]
    ) -> Tuple[float, List[str]]:
        """Format network values as bytes per second."""
        return label_bytes_per_sec(values, idxs)

    def hotkey(self) -> Optional[str]:
        """Return hotkey for network metric."""
        return "n"

    @classmethod
    def configure_argparse(cls, parser: ArgumentParser) -> None:
        """Configure command-line arguments."""
        parser.add_argument(
            "--network",
            type=SimpleMode,
            default=SimpleMode.show,
            choices=list(SimpleMode),
            help='Show network io. Hotkey: "n"',
        )

    def process_data(self, raw_data: Dict[str, Any]) -> Dict[str, float]:
        """Convert collector data to display format with proper titles."""
        result = {}

        # Map collector keys to display titles
        if "rx_bytes_per_sec" in raw_data:
            result["network rx"] = raw_data["rx_bytes_per_sec"]

        if "tx_bytes_per_sec" in raw_data:
            result["network tx"] = raw_data["tx_bytes_per_sec"]

        return result
