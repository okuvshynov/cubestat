from typing import Any, Dict, List, Optional

import psutil
from prometheus_client import Gauge

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
        return float(sum(cpu["utilization"] for cpu in self.cpus) / len(self.cpus))


class CPUCollector(BaseCollector):
    """Base CPU collector."""

    @classmethod
    def collector_id(cls) -> str:
        return "cpu"


@collector_registry.register("linux")
class LinuxCPUCollector(CPUCollector):
    """Linux-specific CPU collector using psutil."""

    def __init__(self):
        # Initialize Prometheus metrics
        self.cpu_utilization_gauge: Optional[Gauge] = None
        self._init_prometheus_metrics()
    
    def _init_prometheus_metrics(self) -> None:
        """Initialize Prometheus Gauge metrics for CPU monitoring."""
        try:
            self.cpu_utilization_gauge = Gauge(
                'cpu_usage_percent',
                'CPU core utilization percentage',
                labelnames=['core_id', 'cluster_id', 'cluster_type']
            )
        except Exception:
            # Gauge might already exist if collector is re-initialized
            self.cpu_utilization_gauge = None

    def collect(self, context: Dict[str, Any]) -> Dict[str, float]:
        cpu_load = psutil.cpu_percent(percpu=True)
        
        result = {}
        
        # Add individual core metrics
        for i, utilization in enumerate(cpu_load):
            result[f"cpu.cpu.0.core.{i}.utilization.percent"] = utilization
            
            # Update Prometheus gauge (Linux doesn't have distinct clusters, so use defaults)
            if self.cpu_utilization_gauge is not None:
                self.cpu_utilization_gauge.labels(
                    core_id=str(i),
                    cluster_id="0",
                    cluster_type="generic"
                ).set(utilization)
        
        # Add cluster total (average of all cores)
        cluster_total = sum(cpu_load) / len(cpu_load) if cpu_load else 0.0
        result["cpu.cpu.0.total.utilization.percent"] = cluster_total
        
        # Add total CPU count
        result["cpu.total.count"] = len(cpu_load)
        
        return result


@collector_registry.register("darwin")
class MacOSCPUCollector(CPUCollector):
    """macOS-specific CPU collector using system context."""

    def __init__(self):
        # Initialize Prometheus metrics
        self.cpu_utilization_gauge: Optional[Gauge] = None
        self._init_prometheus_metrics()
    
    def _init_prometheus_metrics(self) -> None:
        """Initialize Prometheus Gauge metrics for CPU monitoring."""
        try:
            self.cpu_utilization_gauge = Gauge(
                'cpu_usage_percent',
                'CPU core utilization percentage',
                labelnames=['core_id', 'cluster_id', 'cluster_type']
            )
        except Exception:
            # Gauge might already exist if collector is re-initialized
            self.cpu_utilization_gauge = None

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
                key = f"cpu.{cluster_name}.{cluster_index}.core.{core_id}.utilization.percent"
                result[key] = utilization
                cluster_utilizations.append(utilization)
                total_cpus += 1
                
                # Update Prometheus gauge with Apple Silicon cluster information
                if self.cpu_utilization_gauge is not None:
                    self.cpu_utilization_gauge.labels(
                        core_id=str(core_id),
                        cluster_id=str(cluster_index),
                        cluster_type=cluster_name
                    ).set(utilization)
            
            # Cluster total (average of cores in this cluster)
            if cluster_utilizations:
                cluster_total = sum(cluster_utilizations) / len(cluster_utilizations)
                key = f"cpu.{cluster_name}.{cluster_index}.total.utilization.percent"
                result[key] = cluster_total

        # Total CPU count
        result["cpu.total.count"] = total_cpus
        
        return result
