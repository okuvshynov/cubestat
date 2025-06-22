from argparse import ArgumentParser
from typing import Any, Dict, List, Optional, Sequence, Tuple

from cubestat.common import DisplayMode, label10
from cubestat.metrics_registry import presenter_registry
from cubestat.presenters.base_presenter import BasePresenter


class PowerMode(DisplayMode):
    combined = "combined"
    all = "all"
    off = "off"


@presenter_registry.register
class PowerPresenter(BasePresenter):
    """Power presenter handling power display modes."""

    def __init__(self):
        self.mode = PowerMode.combined  # type: ignore

    @classmethod
    def key(cls) -> str:
        return "power"

    @classmethod
    def collector_id(cls) -> str:
        return "power"

    def configure(self, config) -> "PowerPresenter":
        # Handle both Dict and Namespace objects
        if hasattr(config, "get"):
            mode_value = config.get("power", PowerMode.combined)
        else:
            mode_value = getattr(config, "power", PowerMode.combined)

        # Ensure we have a proper PowerMode enum, not a string
        if isinstance(mode_value, str):
            self.mode = PowerMode(mode_value)  # type: ignore
        else:
            self.mode = mode_value  # type: ignore
        return self

    def pre(self, title: str) -> Tuple[bool, str]:
        """Filter power metrics based on display mode."""
        if self.mode == PowerMode.off:
            return False, ""
        if self.mode == PowerMode.combined and "total" not in title:
            return False, ""
        if "total" not in title:
            return True, "  "
        return True, ""

    def format(
        self, _title: str, values: Sequence[float], idxs: Sequence[int]
    ) -> Tuple[float, List[str]]:
        """Format power values with proper units (mW, W, kW)."""
        return label10(values, [(1000 * 1000, "kW"), (1000, "W"), (1, "mW")], idxs)

    def hotkey(self) -> Optional[str]:
        """Return hotkey for power metric."""
        return "p"

    @classmethod
    def configure_argparse(cls, parser: ArgumentParser) -> None:
        """Configure command-line arguments."""
        parser.add_argument(
            "--power",
            type=PowerMode,
            default=PowerMode.combined,
            choices=list(PowerMode),
            help='Power: hidden, CPU/GPU/ANE breakdown, or combined usage. Hotkey: "p"',
        )

    def process_data(self, raw_data: Dict[str, Any]) -> Dict[str, float]:
        """Convert collector data to display format with proper titles."""
        result = {}

        # Map collector keys to display titles
        if "total_power" in raw_data:
            result["total power"] = raw_data["total_power"]

        if "ane_power" in raw_data:
            result["ANE power"] = raw_data["ane_power"]

        if "cpu_power" in raw_data:
            result["CPU power"] = raw_data["cpu_power"]

        if "gpu_power" in raw_data:
            result["GPU power"] = raw_data["gpu_power"]

        return result
