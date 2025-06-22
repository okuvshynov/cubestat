from typing import Any, Dict, List

import psutil

from cubestat.collectors.base_collector import BaseCollector
from cubestat.metrics_registry import collector_registry


class CPUCluster:
    """Represents a CPU cluster with individual CPU data."""

    def __init__(self, name: str, cpus: List[Dict[str, Any]]):
        self.name = name
        self.cpus = cpus
        self.total_utilization = self._calculate_total()

    def _calculate_total(self) -> float:
        """Calculate total cluster utilization from individual CPUs."""
        if not self.cpus:
            return 0.0
        return sum(cpu["utilization"] for cpu in self.cpus) / len(self.cpus)


class CPUCollector(BaseCollector):
    """Base CPU collector."""

    @classmethod
    def collector_id(cls) -> str:
        return "cpu"


@collector_registry.register("linux")
class LinuxCPUCollector(CPUCollector):
    """Linux-specific CPU collector using psutil."""

    def collect(self, context: Dict[str, Any]) -> Dict[str, Any]:
        cpu_load = psutil.cpu_percent(percpu=True)

        # Create a single cluster for all CPUs
        cpus = []
        for i, utilization in enumerate(cpu_load):
            cpus.append({"cpu": i, "utilization": utilization})

        cluster = CPUCluster("CPU", cpus)

        return {"clusters": [cluster], "total_cpus": len(cpu_load)}


@collector_registry.register("darwin")
class MacOSCPUCollector(CPUCollector):
    """macOS-specific CPU collector using system context."""

    def collect(self, context: Dict[str, Any]) -> Dict[str, Any]:
        clusters = []
        total_cpus = 0

        for cluster_data in context["processor"]["clusters"]:
            cpus = []
            for cpu_data in cluster_data["cpus"]:
                cpus.append(
                    {"cpu": cpu_data["cpu"], "utilization": 100.0 - 100.0 * cpu_data["idle_ratio"]}
                )

            cluster = CPUCluster(cluster_data["name"], cpus)
            clusters.append(cluster)
            total_cpus += len(cpus)

        return {"clusters": clusters, "total_cpus": total_cpus}
