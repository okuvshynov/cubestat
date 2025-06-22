from typing import Any, Dict

from cubestat.collectors.base_collector import BaseCollector
from cubestat.metrics_registry import collector_registry


class PowerCollector(BaseCollector):
    """Base power collector."""

    @classmethod
    def collector_id(cls) -> str:
        return "power"


@collector_registry.register("darwin")
class MacOSPowerCollector(PowerCollector):
    """macOS-specific power collector using system context."""

    def collect(self, context: Dict[str, Any]) -> Dict[str, float]:
        """Collect power metrics from macOS system context."""
        processor_data = context.get("processor", {})
        return {
            "total_power": processor_data.get("combined_power", 0.0),
            "ane_power": processor_data.get("ane_power", 0.0),
            "cpu_power": processor_data.get("cpu_power", 0.0),
            "gpu_power": processor_data.get("gpu_power", 0.0),
        }


@collector_registry.register("linux")
class LinuxPowerCollector(PowerCollector):
    """Linux-specific power collector (placeholder - power data not available)."""

    def collect(self, context: Dict[str, Any]) -> Dict[str, float]:
        """Linux systems typically don't have detailed power metrics available."""
        # Linux generally doesn't provide detailed power consumption data
        # This is a placeholder that returns zero values
        return {
            "total_power": 0.0,
            "ane_power": 0.0,
            "cpu_power": 0.0,
            "gpu_power": 0.0,
        }
