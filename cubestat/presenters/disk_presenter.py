from typing import List, Sequence, Tuple
from argparse import ArgumentParser

from cubestat.common import SimpleMode, label_bytes_per_sec
from cubestat.presenters.base_presenter import BasePresenter
from cubestat.metrics_registry import presenter_registry


@presenter_registry.register
class DiskPresenter(BasePresenter):
    """Presenter for disk I/O metrics."""
    
    @classmethod
    def key(cls) -> str:
        return 'disk'
    
    @classmethod
    def collector_id(cls) -> str:
        return 'disk'
    
    def hotkey(self) -> str:
        return 'd'
    
    def pre(self, title: str) -> Tuple[bool, str]:
        if self.mode == SimpleMode.hide:
            return False, ''
        return True, ''
    
    def format(self, title: str, values: Sequence[float], idxs: Sequence[int]) -> Tuple[float, List[str]]:
        return label_bytes_per_sec(values, idxs)
    
    @classmethod
    def configure_argparse(cls, parser: ArgumentParser) -> None:
        parser.add_argument(
            '--disk',
            type=SimpleMode,
            default=SimpleMode.show,
            choices=list(SimpleMode),
            help='Show disk read/write rate. Hotkey: "d"'
        )
    
    def configure(self, config) -> 'DiskPresenter':
        self.mode = config.disk
        return self