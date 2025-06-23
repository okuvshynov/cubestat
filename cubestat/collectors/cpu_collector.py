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

    def collect(self, context: Dict[str, Any]) -> Dict[str, float]:
        cpu_load = psutil.cpu_percent(percpu=True)
        
        result = {}
        
        # Add individual core metrics
        for i, utilization in enumerate(cpu_load):
            result[f"cpu.cpu.0.core.{i}.utilization.percent"] = utilization
        
        # Add cluster total (average of all cores)
        cluster_total = sum(cpu_load) / len(cpu_load) if cpu_load else 0.0
        result["cpu.cpu.0.total.utilization.percent"] = cluster_total
        
        # Add total CPU count
        result["cpu.total.count"] = len(cpu_load)
        
        return result


@collector_registry.register("darwin")
class MacOSCPUCollector(CPUCollector):
    """macOS-specific CPU collector using system context."""

    def collect(self, context: Dict[str, Any]) -> Dict[str, float]:
        result = {}
        total_cpus = 0

        for cluster_index, cluster_data in enumerate(context["processor"]["clusters"]):
            cluster_name = cluster_data["name"].lower()  # "Performance" -> "performance"
            cluster_utilizations = []
            
            for cpu_data in cluster_data["cpus"]:
                core_id = cpu_data["cpu"]
                utilization = 100.0 - 100.0 * cpu_data["idle_ratio"]
                
                # Individual core metric
                result[f"cpu.{cluster_name}.{cluster_index}.core.{core_id}.utilization.percent"] = utilization
                cluster_utilizations.append(utilization)
                total_cpus += 1
            
            # Cluster total (average of cores in this cluster)
            if cluster_utilizations:
                cluster_total = sum(cluster_utilizations) / len(cluster_utilizations)
                result[f"cpu.{cluster_name}.{cluster_index}.total.utilization.percent"] = cluster_total

        # Total CPU count
        result["cpu.total.count"] = total_cpus
        
        return result
