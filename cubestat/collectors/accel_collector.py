import subprocess
from typing import Any, Dict

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

        return {"accel.ane.utilization.percent": ane_util_percent}
