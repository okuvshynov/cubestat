# various ML accelerators, for now supports apple's NE
import subprocess
from cubestat.metrics.base_metric import base_metric
from cubestat.metrics.registry import cubestat_metric

@cubestat_metric
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
        ane_scaler = 15500 # default to M2
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
    
    def pre(self, mode, title):
        return True, ''
    
    def format(self, values, idxs):
        return 100.0, [f'{values[i]:3.0f}%' for i in idxs]

    @classmethod
    def key(cls):
        return 'ane'

    @classmethod
    def supported_platforms(cls):
        return ['macos']
