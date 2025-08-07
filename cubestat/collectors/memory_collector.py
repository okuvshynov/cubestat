from typing import Any, Dict, Optional

import psutil
from prometheus_client import Gauge

from cubestat.collectors.base_collector import BaseCollector
from cubestat.metrics_registry import collector_registry


class MemoryCollector(BaseCollector):
    """Base memory collector."""

    @classmethod
    def collector_id(cls) -> str:
        return "memory"


@collector_registry.register("darwin")
class MacOSMemoryCollector(MemoryCollector):
    """macOS-specific memory collector using psutil."""

    def __init__(self):
        # Initialize Prometheus metrics
        self.memory_used_percent_gauge: Optional[Gauge] = None
        self.memory_used_bytes_gauge: Optional[Gauge] = None
        self.memory_wired_bytes_gauge: Optional[Gauge] = None
        self._init_prometheus_metrics()
    
    def _init_prometheus_metrics(self) -> None:
        """Initialize Prometheus Gauge metrics for memory monitoring."""
        try:
            self.memory_used_percent_gauge = Gauge(
                'memory_usage_percent',
                'Memory usage percentage'
            )
            self.memory_used_bytes_gauge = Gauge(
                'memory_used_bytes',
                'Memory used in bytes'
            )
            self.memory_wired_bytes_gauge = Gauge(
                'memory_wired_bytes',
                'Wired memory in bytes (macOS)'
            )
        except Exception:
            # Gauges might already exist if collector is re-initialized
            self.memory_used_percent_gauge = None
            self.memory_used_bytes_gauge = None
            self.memory_wired_bytes_gauge = None

    def collect(self, context: Dict[str, Any]) -> Dict[str, float]:
        vm = psutil.virtual_memory()
        
        # Update Prometheus gauges
        if self.memory_used_percent_gauge is not None:
            self.memory_used_percent_gauge.set(vm.percent)
        if self.memory_used_bytes_gauge is not None:
            self.memory_used_bytes_gauge.set(vm.used)
        if self.memory_wired_bytes_gauge is not None:
            self.memory_wired_bytes_gauge.set(vm.wired)
        
        return {
            "memory.system.total.used.percent": vm.percent,
            "memory.system.total.used.bytes": vm.used,
            "memory.system.wired.bytes": vm.wired,
        }


@collector_registry.register("linux")
class LinuxMemoryCollector(MemoryCollector):
    """Linux-specific memory collector reading /proc/meminfo."""

    def __init__(self):
        # Initialize Prometheus metrics
        self.memory_used_percent_gauge: Optional[Gauge] = None
        self.memory_used_bytes_gauge: Optional[Gauge] = None
        self.memory_mapped_bytes_gauge: Optional[Gauge] = None
        self._init_prometheus_metrics()
    
    def _init_prometheus_metrics(self) -> None:
        """Initialize Prometheus Gauge metrics for memory monitoring."""
        try:
            self.memory_used_percent_gauge = Gauge(
                'memory_usage_percent',
                'Memory usage percentage'
            )
            self.memory_used_bytes_gauge = Gauge(
                'memory_used_bytes',
                'Memory used in bytes'
            )
            self.memory_mapped_bytes_gauge = Gauge(
                'memory_mapped_bytes',
                'Mapped memory in bytes (Linux)'
            )
        except Exception:
            # Gauges might already exist if collector is re-initialized
            self.memory_used_percent_gauge = None
            self.memory_used_bytes_gauge = None
            self.memory_mapped_bytes_gauge = None

    def collect(self, context: Dict[str, Any]) -> Dict[str, float]:
        meminfo = {}
        with open("/proc/meminfo", "r") as f:
            for line in f:
                key, value = line.split(":", 1)
                meminfo[key.strip()] = int(value.split()[0]) * 1024

        used_percent = 100.0 * (meminfo["MemTotal"] - meminfo["MemAvailable"]) / meminfo["MemTotal"]
        used_bytes = meminfo["MemTotal"] - meminfo["MemAvailable"]
        mapped_bytes = meminfo["Mapped"]
        
        # Update Prometheus gauges
        if self.memory_used_percent_gauge is not None:
            self.memory_used_percent_gauge.set(used_percent)
        if self.memory_used_bytes_gauge is not None:
            self.memory_used_bytes_gauge.set(used_bytes)
        if self.memory_mapped_bytes_gauge is not None:
            self.memory_mapped_bytes_gauge.set(mapped_bytes)

        return {
            "memory.system.total.used.percent": used_percent,
            "memory.system.total.used.bytes": used_bytes,
            "memory.system.mapped.bytes": mapped_bytes,
        }
