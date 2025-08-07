import subprocess
from typing import Any, Dict, Optional

from prometheus_client import Gauge

from cubestat.collectors.base_collector import BaseCollector
from cubestat.metrics_registry import collector_registry


class AccelCollector(BaseCollector):
    """Base accelerator (ANE) collector."""

    @classmethod
    def collector_id(cls) -> str:
        return "accel"


@collector_registry.register("darwin")
class MacOSAccelCollector(AccelCollector):
    """macOS-specific Apple Neural Engine (ANE) collector."""

    def __init__(self):
        self.ane_scaler = self._get_ane_scaler()
        
        # Initialize Prometheus metrics
        self.ane_utilization_gauge: Optional[Gauge] = None
        self._init_prometheus_metrics()
    
    def _init_prometheus_metrics(self) -> None:
        """Initialize Prometheus Gauge metrics for ANE monitoring."""
        try:
            self.ane_utilization_gauge = Gauge(
                'ane_usage_percent',
                'Apple Neural Engine (ANE) utilization percentage'
            )
        except Exception:
            # Gauge might already exist if collector is re-initialized
            # For now, we'll just set it to None and handle it gracefully
            self.ane_utilization_gauge = None

    def _get_ane_scaler(self) -> float:
        """Determine ANE power scaler based on Apple Silicon chip model."""
        # This is pretty much a guess based on tests on a few models available.
        # Need anything M3 + Ultra models to test.
        # Based on TOPS numbers Apple published, all models seem to have same ANE
        # except Ultra having 2x.
        ane_power_scalers = {
            "M1": 13000.0,
            "M2": 15500.0,
            "M3": 15500.0,
        }

        # Identify the model to get ANE scaler
        brand_str = subprocess.check_output(["sysctl", "-n", "machdep.cpu.brand_string"], text=True)
        ane_scaler = 15500.0  # default to M2

        for k, v in ane_power_scalers.items():
            if k in brand_str:
                ane_scaler = v
                if "ultra" in brand_str.lower():
                    ane_scaler *= 2
                break

        return ane_scaler

    def collect(self, context: Dict[str, Any]) -> Dict[str, float]:
        """Collect ANE utilization from macOS system context."""
        processor_data = context.get("processor", {})
        ane_power = processor_data.get("ane_power", 0.0)

        # Calculate ANE utilization as percentage
        ane_util_percent = 100.0 * ane_power / self.ane_scaler
        
        # Update Prometheus gauge (no-op for now, but sets the value)
        if self.ane_utilization_gauge is not None:
            self.ane_utilization_gauge.set(ane_util_percent)

        return {"accel.ane.utilization.percent": ane_util_percent}
