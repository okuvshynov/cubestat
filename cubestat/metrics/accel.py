from argparse import ArgumentParser
from typing import Any, Dict

from cubestat.metrics.metric_adapter import MetricAdapter
from cubestat.metrics_registry import collector_registry, cubestat_metric, presenter_registry


class AccelMetricAdapter(MetricAdapter):
    """Accelerator (ANE) metric adapter handling data processing."""

    def read(self, context: Dict[str, Any]) -> Dict[str, float]:
        """Read ANE data and convert to display format."""
        raw_data = self.collector.collect(context)
        return self.presenter.process_data(raw_data)

    @classmethod
    def key(cls) -> str:
        return "ane"

    @classmethod
    def configure_argparse(cls, _parser: ArgumentParser) -> None:
        # ANE metric doesn't have command-line arguments
        pass


@cubestat_metric("darwin")
class ane_metric(AccelMetricAdapter):
    """macOS ANE metric using new collector/presenter architecture."""

    def __init__(self):
        collector = collector_registry.get_instance("darwin", "accel")
        presenter = presenter_registry.get_instance("accel")
        super().__init__(collector, presenter)


# Linux ANE metric not applicable - ANE (Apple Neural Engine) is Apple Silicon specific
# No equivalent accelerator hardware with standard APIs on Linux systems

# Keep old implementation commented for reference
"""
import subprocess
from cubestat.metrics.base_metric import base_metric
from cubestat.metrics_registry import cubestat_metric


@cubestat_metric('darwin')
class ane_metric(base_metric):
    def __init__(self) -> None:
        self.ane_scaler = self.get_ane_scaler()

    def get_ane_scaler(self) -> float:
        # This is pretty much a guess based on tests on a few models I had available.
        # Need anything M3 + Ultra models to test.
        # Based on TOPS numbers Apple published, all models seem to have same ANE
        # except Ultra having 2x.
        ane_power_scalers = {
            "M1": 13000.0,
            "M2": 15500.0,
            "M3": 15500.0,
        }
        # identity the model to get ANE scaler
        brand_str = subprocess.check_output(['sysctl', '-n', 'machdep.cpu.brand_string'], text=True)
        ane_scaler = 15500  # default to M2
        for k, v in ane_power_scalers.items():
            if k in brand_str:
                ane_scaler = v
                if 'ultra' in brand_str.lower():
                    ane_scaler *= 2
                break
        return ane_scaler

    def read(self, context):
        res = {}
        res['ANE util %'] = 100.0 * context['processor']['ane_power'] / self.ane_scaler
        return res

    def pre(self, title):
        return True, ''

    def format(self, title, values, idxs):
        return 100.0, [f'{values[i]:3.0f}%' for i in idxs]

    @classmethod
    def key(cls):
        return 'ane'
"""
