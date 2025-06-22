from argparse import ArgumentParser
from typing import Any, Dict, List, Optional, Sequence, Tuple

from cubestat.collectors.base_collector import BaseCollector
from cubestat.metrics.base_metric import base_metric
from cubestat.presenters.base_presenter import BasePresenter


class MetricAdapter(base_metric):
    """Adapter to use new collector/presenter architecture with existing metric system."""

    def __init__(self, collector: BaseCollector, presenter: BasePresenter):
        self.collector = collector
        self.presenter = presenter

    def read(self, context: Dict[str, Any]) -> Dict[str, float]:
        """Read data using the collector."""
        raw_data = self.collector.collect(context)
        # Map collector output to expected format
        result = {}
        for key, value in raw_data.items():
            # Convert underscores to spaces for display
            display_key = key.replace("_", " ")
            result[display_key] = value
        return result

    def pre(self, title: str) -> Tuple[bool, str]:
        """Delegate to presenter."""
        return self.presenter.pre(title)

    def format(
        self, title: str, values: Sequence[float], idxs: Sequence[int]
    ) -> Tuple[float, List[str]]:
        """Delegate to presenter."""
        return self.presenter.format(title, values, idxs)

    @classmethod
    def key(cls) -> str:
        """This should be overridden by subclasses."""
        raise NotImplementedError

    def hotkey(self) -> Optional[str]:
        """Delegate to presenter."""
        return self.presenter.hotkey()

    @classmethod
    def configure_argparse(cls, parser: ArgumentParser) -> None:
        """This should be overridden by subclasses."""
        pass

    @property
    def mode(self):
        """Get the current display mode from the presenter."""
        return self.presenter.mode

    @mode.setter
    def mode(self, value):
        """Set the display mode on the presenter."""
        self.presenter.mode = value

    def configure(self, config: Dict[str, Any]) -> "MetricAdapter":
        """Configure both collector and presenter."""
        self.collector.configure(config)
        self.presenter.configure(config)
        return self
