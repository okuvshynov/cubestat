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


    def configure(self, config) -> "CPUPresenter":
        self.mode = getattr(config, "cpu", auto_cpu_mode())
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
        """Process CPU data from collector."""
        result = {}
        
        # Check if we have standardized metrics (from collector)
        has_standardized = any(k.startswith("cpu.") and k != "cpu.total.count" for k in raw_data.keys())
        
        if has_standardized:
            # Handle standardized metric names directly
            cpu_clusters = {}

            # First pass: collect all CPU metrics by cluster
            for key, value in raw_data.items():
                if key.startswith("cpu.") and key != "cpu.total.count":
                    parts = key.split(".")
                    if len(parts) >= 7 and parts[3] == "core":
                        # Individual core: cpu.performance.0.core.2.utilization.percent
                        cluster_name = parts[1].capitalize()
                        cluster_index = parts[2]
                        core_id = parts[4]
                        cluster_key = f"{cluster_name}.{cluster_index}"

                        if cluster_key not in cpu_clusters:
                            cpu_clusters[cluster_key] = {
                                "cores": {},
                                "total_key": None,
                                "total_value": None,
                            }

                        cpu_clusters[cluster_key]["cores"][core_id] = value

                    elif len(parts) >= 6 and parts[3] == "total":
                        # Cluster total: cpu.performance.0.total.utilization.percent
                        cluster_name = parts[1].capitalize()
                        cluster_index = parts[2]
                        cluster_key = f"{cluster_name}.{cluster_index}"

                        if cluster_key not in cpu_clusters:
                            cpu_clusters[cluster_key] = {
                                "cores": {},
                                "total_key": None,
                                "total_value": None,
                            }

                        cpu_clusters[cluster_key]["total_key"] = key
                        cpu_clusters[cluster_key]["total_value"] = value

            # Second pass: build ordered output (cluster total, then its cores)
            # Sort clusters by minimum CPU ID to preserve original order
            # (Performance cores typically have lower IDs)
            def cluster_sort_key(item):
                cluster_key, cluster_data = item
                if cluster_data["cores"]:
                    return min(int(core_id) for core_id in cluster_data["cores"].keys())
                return float("inf")

            self.cpu_clusters = []
            for cluster_key, cluster_data in sorted(cpu_clusters.items(), key=cluster_sort_key):
                cluster_name = cluster_key.split(".")[0]

                # Add cluster total first
                if cluster_data["total_value"] is not None:
                    core_count = len(cluster_data["cores"])
                    cluster_title = f"[{core_count}] {cluster_name} total CPU util %"
                    result[cluster_title] = cluster_data["total_value"]
                    self.cpu_clusters.append(cluster_title)

                # Then add individual cores in order
                for core_id in sorted(cluster_data["cores"].keys(), key=int):
                    cpu_title = f"{cluster_name} CPU {core_id} util %"
                    result[cpu_title] = cluster_data["cores"][core_id]
        else:
            # Legacy support for pre-transformed data (backward compatibility)
            # Extract cluster titles for filtering
            self.cpu_clusters = []
            for key in raw_data.keys():
                if "total CPU util %" in key:
                    self.cpu_clusters.append(key)
            
            result = raw_data
        
        return result
