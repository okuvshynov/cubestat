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
            "memory.system.total.used.percent": vm.percent,
            "memory.system.total.used.bytes": vm.used,
            "memory.system.wired.bytes": vm.wired,
        }


@collector_registry.register("linux")
class LinuxMemoryCollector(MemoryCollector):
    """Linux-specific memory collector reading /proc/meminfo."""

    def collect(self, context: Dict[str, Any]) -> Dict[str, float]:
        meminfo = {}
        with open("/proc/meminfo", "r") as f:
            for line in f:
                key, value = line.split(":", 1)
                meminfo[key.strip()] = int(value.split()[0]) * 1024

        return {
            "memory.system.total.used.percent": 100.0
            * (meminfo["MemTotal"] - meminfo["MemAvailable"])
            / meminfo["MemTotal"],
            "memory.system.total.used.bytes": meminfo["MemTotal"] - meminfo["MemAvailable"],
            "memory.system.mapped.bytes": meminfo["Mapped"],
        }
