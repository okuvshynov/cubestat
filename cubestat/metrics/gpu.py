from argparse import ArgumentParser
from typing import Any, Dict

from cubestat.metrics.metric_adapter import MetricAdapter
from cubestat.metrics_registry import collector_registry, cubestat_metric, presenter_registry


class GPUMetricAdapter(MetricAdapter):
    """GPU metric adapter handling multi-vendor GPU data processing."""

    def read(self, context: Dict[str, Any]) -> Dict[str, float]:
        """Read GPU data and convert to display format."""
        raw_data = self.collector.collect(context)
        return self.presenter.process_data(raw_data)

    @classmethod
    def key(cls) -> str:
        return "gpu"

    @classmethod
    def configure_argparse(cls, parser: ArgumentParser) -> None:
        # Get presenter class to configure argparse
        presenter_cls = presenter_registry.get("gpu")
        if presenter_cls:
            presenter_cls.configure_argparse(parser)




@cubestat_metric("linux")
class unified_gpu_metric_linux(GPUMetricAdapter):
    """Linux GPU metric using new collector/presenter architecture."""

    def __init__(self):
        collector = collector_registry.get_instance("linux", "gpu")
        presenter = presenter_registry.get_instance("gpu")
        super().__init__(collector, presenter)


@cubestat_metric("darwin")
class unified_gpu_metric_macos(GPUMetricAdapter):
    """macOS GPU metric using new collector/presenter architecture."""

    def __init__(self):
        collector = collector_registry.get_instance("darwin", "gpu")
        presenter = presenter_registry.get_instance("gpu")
        super().__init__(collector, presenter)


# Keep old implementation commented for reference
"""
import logging
import subprocess
from abc import ABC, abstractmethod
from importlib.util import find_spec
from typing import Any, Dict, List, Sequence, Tuple

from cubestat.common import DisplayMode
from cubestat.metrics.base_metric import base_metric
from cubestat.metrics_registry import cubestat_metric

# Setup logging
logger = logging.getLogger(__name__)


class GPUMode(DisplayMode):
    collapsed = "collapsed"
    load_only = "load_only"
    load_and_vram = "load_and_vram"


class gpu_metric(base_metric):
    n_gpus: int
    mode: GPUMode

    def pre(self, title: str) -> Tuple[bool, str]:
        if self.n_gpus > 0 and self.mode == GPUMode.collapsed and "Total GPU" not in title:
            return False, ""
        if self.mode == GPUMode.load_only and "vram" in title:
            return False, ""
        if self.n_gpus > 1 and "Total GPU" not in title:
            return True, "  "
        return True, ""

    def format(
        self, title: str, values: Sequence[float], idxs: Sequence[int]
    ) -> Tuple[float, List[str]]:
        return 100.0, [f"{values[i]:3.0f}%" for i in idxs]

    def configure(self, conf: Any) -> "gpu_metric":
        self.mode = conf.gpu
        return self

    @classmethod
    def key(cls) -> str:
        return "gpu"

    def hotkey(self) -> str:
        return "g"

    @classmethod
    def configure_argparse(cls, parser: Any) -> None:
        parser.add_argument(
            "--gpu",
            type=GPUMode,
            default=GPUMode.load_only,
            choices=list(GPUMode),
            help='GPU mode - hidden, load, or load and vram usage. Hotkey: "g"',
        )


class GPUHandler(ABC):
    [... handler classes ...]


@cubestat_metric("linux")
class unified_gpu_metric_linux(gpu_metric):
    [... original Linux implementation ...]


@cubestat_metric("darwin")
class unified_gpu_metric_macos(gpu_metric):
    [... original macOS implementation ...]
"""