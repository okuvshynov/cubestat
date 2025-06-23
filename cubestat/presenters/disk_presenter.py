from argparse import ArgumentParser
from typing import Any, Dict, List, Optional, Sequence, Tuple

from cubestat.common import SimpleMode, label_bytes_per_sec
from cubestat.metrics_registry import presenter_registry
from cubestat.presenters.base_presenter import BasePresenter


@presenter_registry.register
class DiskPresenter(BasePresenter):
    """Presenter for disk I/O metrics."""

    @classmethod
    def key(cls) -> str:
        return "disk"


    def hotkey(self) -> Optional[str]:
        return "d"

    def pre(self, _title: str) -> Tuple[bool, str]:
        if self.mode == SimpleMode.hide:
            return False, ""
        return True, ""

    def format(
        self, _title: str, values: Sequence[float], idxs: Sequence[int]
    ) -> Tuple[float, List[str]]:
        return label_bytes_per_sec(values, idxs)

    @classmethod
    def configure_argparse(cls, parser: ArgumentParser) -> None:
        parser.add_argument(
            "--disk",
            type=SimpleMode,
            default=SimpleMode.show,
            choices=list(SimpleMode),
            help='Show disk read/write rate. Hotkey: "d"',
        )

    def configure(self, config) -> "DiskPresenter":
        self.mode = getattr(config, "disk", SimpleMode.show)
        return self

    def process_data(self, raw_data: Dict[str, Any]) -> Dict[str, float]:
        """Convert collector data to display format with proper titles."""
        result = {}

        # Map collector keys to display titles
        if "disk_read" in raw_data:
            result["disk read"] = raw_data["disk_read"]

        if "disk_write" in raw_data:
            result["disk write"] = raw_data["disk_write"]

        return result
