import os
from argparse import ArgumentParser
from typing import Any, Dict, List, Optional, Sequence, Tuple

from cubestat.common import DisplayMode
from cubestat.metrics_registry import presenter_registry
from cubestat.presenters.base_presenter import BasePresenter


class CPUMode(DisplayMode):
    all = "all"
    by_cluster = "by_cluster"
    by_core = "by_core"


def auto_cpu_mode() -> CPUMode:
    cpu_count = os.cpu_count()
    return CPUMode.all if cpu_count is not None and cpu_count < 20 else CPUMode.by_cluster


@presenter_registry.register
class CPUPresenter(BasePresenter):
    """CPU presenter handling hierarchical display modes."""

    def __init__(self):
        self.mode = auto_cpu_mode()  # type: ignore
        self.cpu_clusters = []

    @classmethod
    def key(cls) -> str:
        return "cpu"

    @classmethod
    def collector_id(cls) -> str:
        return "cpu"

    def configure(self, config) -> "CPUPresenter":
        # Handle both Dict and Namespace objects
        if hasattr(config, "get"):
            mode_value = config.get("cpu", auto_cpu_mode())
        else:
            mode_value = getattr(config, "cpu", auto_cpu_mode())

        # Ensure we have a proper CPUMode enum, not a string
        if isinstance(mode_value, str):
            self.mode = CPUMode(mode_value)  # type: ignore
        else:
            self.mode = mode_value  # type: ignore
        return self

    def pre(self, title: str) -> Tuple[bool, str]:
        """Filter titles based on display mode."""
        if self.mode == CPUMode.by_cluster and title not in self.cpu_clusters:
            return False, ""
        if self.mode == CPUMode.by_core and title in self.cpu_clusters:
            return False, ""
        if self.mode == CPUMode.all and title not in self.cpu_clusters:
            return True, "  "
        else:
            return True, ""

    def format(
        self, title: str, values: Sequence[float], idxs: Sequence[int]
    ) -> Tuple[float, List[str]]:
        """Format CPU utilization as percentages."""
        return 100.0, [f"{values[i]:3.0f}%" for i in idxs]

    def hotkey(self) -> Optional[str]:
        """Return hotkey for CPU metric."""
        return "c"

    @classmethod
    def configure_argparse(cls, parser: ArgumentParser) -> None:
        """Configure command-line arguments."""
        parser.add_argument(
            "--cpu",
            type=CPUMode,
            default=auto_cpu_mode(),
            choices=list(CPUMode),
            help='Select CPU mode: all cores, cumulative by cluster, or both. Hotkey: "c".',
        )

    def process_data(self, raw_data: Dict[str, Any]) -> Dict[str, float]:
        """Convert collector data to display format."""
        # Check if this is new flat format (from transformer) or old cluster format
        if "clusters" in raw_data:
            # Old format with clusters - convert to flat format
            self.cpu_clusters = []
            result = {}

            for cluster in raw_data["clusters"]:
                # Add cluster total
                cluster_title = f"[{len(cluster.cpus)}] {cluster.name} total CPU util %"
                self.cpu_clusters.append(cluster_title)
                result[cluster_title] = cluster.total_utilization

                # Add individual CPUs
                for cpu in cluster.cpus:
                    cpu_title = f"{cluster.name} CPU {cpu['cpu']} util %"
                    result[cpu_title] = cpu["utilization"]

            return result
        else:
            # New flat format (from transformer) - extract cluster info and return as-is
            self.cpu_clusters = []
            for key in raw_data.keys():
                if "total CPU util %" in key:
                    self.cpu_clusters.append(key)
            
            return raw_data
