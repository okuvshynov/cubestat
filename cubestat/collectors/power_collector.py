from typing import Any, Dict, Optional

from prometheus_client import Gauge

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

    def __init__(self):
        # Initialize Prometheus metrics
        self.power_total_gauge: Optional[Gauge] = None
        self.power_component_gauge: Optional[Gauge] = None
        self._init_prometheus_metrics()
    
    def _init_prometheus_metrics(self) -> None:
        """Initialize Prometheus Gauge metrics for power monitoring."""
        try:
            self.power_total_gauge = Gauge(
                'power_consumption_total_watts',
                'Total power consumption in watts'
            )
            self.power_component_gauge = Gauge(
                'power_consumption_watts',
                'Power consumption by component in watts',
                labelnames=['component']
            )
        except Exception:
            # Gauges might already exist if collector is re-initialized
            self.power_total_gauge = None
            self.power_component_gauge = None

    def collect(self, context: Dict[str, Any]) -> Dict[str, float]:
        """Collect power metrics from macOS system context."""
        processor_data = context.get("processor", {})
        
        total_power = processor_data.get("combined_power", 0.0)
        ane_power = processor_data.get("ane_power", 0.0)
        cpu_power = processor_data.get("cpu_power", 0.0)
        gpu_power = processor_data.get("gpu_power", 0.0)
        
        # Update Prometheus gauges
        if self.power_total_gauge is not None:
            self.power_total_gauge.set(total_power)
        
        if self.power_component_gauge is not None:
            self.power_component_gauge.labels(component="ane").set(ane_power)
            self.power_component_gauge.labels(component="cpu").set(cpu_power)
            self.power_component_gauge.labels(component="gpu").set(gpu_power)
        
        return {
            "power.component.total.consumption.watts": total_power,
            "power.component.ane.consumption.watts": ane_power,
            "power.component.cpu.consumption.watts": cpu_power,
            "power.component.gpu.consumption.watts": gpu_power,
        }


@collector_registry.register("linux")
class LinuxPowerCollector(PowerCollector):
    """Linux-specific power collector (placeholder - power data not available)."""

    def __init__(self):
        # Initialize Prometheus metrics
        self.power_total_gauge: Optional[Gauge] = None
        self.power_component_gauge: Optional[Gauge] = None
        self._init_prometheus_metrics()
    
    def _init_prometheus_metrics(self) -> None:
        """Initialize Prometheus Gauge metrics for power monitoring."""
        try:
            self.power_total_gauge = Gauge(
                'power_consumption_total_watts',
                'Total power consumption in watts'
            )
            self.power_component_gauge = Gauge(
                'power_consumption_watts',
                'Power consumption by component in watts',
                labelnames=['component']
            )
        except Exception:
            # Gauges might already exist if collector is re-initialized
            self.power_total_gauge = None
            self.power_component_gauge = None

    def collect(self, context: Dict[str, Any]) -> Dict[str, float]:
        """Linux systems typically don't have detailed power metrics available."""
        # Linux generally doesn't provide detailed power consumption data
        # This is a placeholder that returns zero values
        
        # Update Prometheus gauges with zero values
        if self.power_total_gauge is not None:
            self.power_total_gauge.set(0.0)
        
        if self.power_component_gauge is not None:
            self.power_component_gauge.labels(component="ane").set(0.0)
            self.power_component_gauge.labels(component="cpu").set(0.0)
            self.power_component_gauge.labels(component="gpu").set(0.0)
        
        return {
            "power.component.total.consumption.watts": 0.0,
            "power.component.ane.consumption.watts": 0.0,
            "power.component.cpu.consumption.watts": 0.0,
            "power.component.gpu.consumption.watts": 0.0,
        }
