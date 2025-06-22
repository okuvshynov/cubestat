from argparse import ArgumentParser
from typing import List, Optional, Sequence, Tuple

from cubestat.common import SimpleMode, label_bytes_per_sec
from cubestat.metrics_registry import presenter_registry
from cubestat.presenters.base_presenter import BasePresenter


@presenter_registry.register
class DiskPresenter(BasePresenter):
    """Presenter for disk I/O metrics."""

    @classmethod
    def key(cls) -> str:
        return "disk"

    @classmethod
    def collector_id(cls) -> str:
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
        # Handle both Dict and Namespace objects
        if hasattr(config, "get"):
            mode_value = config.get("disk", SimpleMode.show)
        else:
            mode_value = getattr(config, "disk", SimpleMode.show)

        # Ensure we have a proper SimpleMode enum, not a string
        if isinstance(mode_value, str):
            self.mode = SimpleMode(mode_value)
        else:
            self.mode = mode_value
        return self
