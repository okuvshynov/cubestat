from argparse import ArgumentParser
from typing import Any, Dict, List, Optional, Sequence, Tuple

from cubestat.common import DisplayMode, label_bytes
from cubestat.metrics_registry import presenter_registry
from cubestat.presenters.base_presenter import BasePresenter


class RAMMode(DisplayMode):
    percent = "percent"
    all = "all"


@presenter_registry.register
class MemoryPresenter(BasePresenter):
    """Memory presenter handling RAM display modes."""

    def __init__(self):
        self.mode = RAMMode.all  # type: ignore

    @classmethod
    def key(cls) -> str:
        return "memory"


    def configure(self, config) -> "MemoryPresenter":
        self.mode = getattr(config, "memory", RAMMode.all)
        return self

    def pre(self, title: str) -> Tuple[bool, str]:
        """Filter memory metrics based on display mode."""
        if title == "RAM used %":
            return True, ""
        if self.mode == RAMMode.all:
            return True, "  "
        return False, ""

    def format(
        self, title: str, values: Sequence[float], idxs: Sequence[int]
    ) -> Tuple[float, List[str]]:
        """Format memory values - percentage for RAM used %, bytes for others."""
        if title == "RAM used %":
            return 100.0, [f"{values[i]:3.0f}%" for i in idxs]
        return label_bytes(values, idxs)

    def hotkey(self) -> Optional[str]:
        """Return hotkey for memory metric."""
        return "m"

    @classmethod
    def configure_argparse(cls, parser: ArgumentParser) -> None:
        """Configure command-line arguments."""
        parser.add_argument(
            "--memory",
            type=RAMMode,
            default=RAMMode.all,
            choices=list(RAMMode),
            help='Select memory mode: percent only or all details. Hotkey: "m".',
        )

    def process_data(self, raw_data: Dict[str, Any]) -> Dict[str, float]:
        """Convert collector data to display format with proper titles."""
        result = {}

        # Handle standardized metric names from collector
        if "memory.system.total.used.percent" in raw_data:
            result["RAM used %"] = raw_data["memory.system.total.used.percent"]

        if "memory.system.total.used.bytes" in raw_data:
            result["RAM used"] = raw_data["memory.system.total.used.bytes"]

        if "memory.system.wired.bytes" in raw_data:  # macOS
            result["RAM wired"] = raw_data["memory.system.wired.bytes"]

        if "memory.system.mapped.bytes" in raw_data:  # Linux
            result["RAM mapped"] = raw_data["memory.system.mapped.bytes"]

        return result
