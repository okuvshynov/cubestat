from typing import Any, Dict

import psutil

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

    def collect(self, context: Dict[str, Any]) -> Dict[str, float]:
        vm = psutil.virtual_memory()
        return {
            "used_percent": vm.percent,
            "used_bytes": vm.used,
            "wired_bytes": vm.wired,
        }


@collector_registry.register("linux")
class LinuxMemoryCollector(MemoryCollector):
    """Linux-specific memory collector reading /proc/meminfo."""

    def __init__(self):
        # Define how to calculate metrics from meminfo data
        self.calculations = {
            "used_percent": lambda mi: 100.0
            * (mi["MemTotal"] - mi["MemAvailable"])
            / mi["MemTotal"],
            "used_bytes": lambda mi: mi["MemTotal"] - mi["MemAvailable"],
            "mapped_bytes": lambda mi: mi["Mapped"],
        }

    def collect(self, context: Dict[str, Any]) -> Dict[str, float]:
        meminfo = {}
        with open("/proc/meminfo", "r") as f:
            for line in f:
                key, value = line.split(":", 1)
                meminfo[key.strip()] = int(value.split()[0]) * 1024

        return {key: calc(meminfo) for key, calc in self.calculations.items()}
