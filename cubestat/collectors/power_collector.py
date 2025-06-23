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
            "power.component.total.consumption.watts": processor_data.get("combined_power", 0.0),
            "power.component.ane.consumption.watts": processor_data.get("ane_power", 0.0),
            "power.component.cpu.consumption.watts": processor_data.get("cpu_power", 0.0),
            "power.component.gpu.consumption.watts": processor_data.get("gpu_power", 0.0),
        }


@collector_registry.register("linux")
class LinuxPowerCollector(PowerCollector):
    """Linux-specific power collector (placeholder - power data not available)."""

    def collect(self, context: Dict[str, Any]) -> Dict[str, float]:
        """Linux systems typically don't have detailed power metrics available."""
        # Linux generally doesn't provide detailed power consumption data
        # This is a placeholder that returns zero values
        return {
            "power.component.total.consumption.watts": 0.0,
            "power.component.ane.consumption.watts": 0.0,
            "power.component.cpu.consumption.watts": 0.0,
            "power.component.gpu.consumption.watts": 0.0,
        }
