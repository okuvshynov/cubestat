import subprocess
from importlib.util import find_spec

# reading compute/memory utilization for nvidia cards. 
class NVReader:
    def __init__(self):
        self.has_nvidia = False
        try:
            subprocess.check_output('nvidia-smi')
            nvspec = find_spec('pynvml')
            if nvspec is not None:
                from pynvml.smi import nvidia_smi
                self.nvsmi = nvidia_smi.getInstance()
                self.has_nvidia = True
        except Exception:
            # TODO: add logging here
            pass

    def read(self):
        res = {}
        if self.has_nvidia:
            for i, v in enumerate(self.nvsmi.DeviceQuery('utilization.gpu,memory.total,memory.used')['gpu']):
                res[f'GPU {i} util %'] = v['utilization']['gpu_util']
                res[f'GPU {i} memory used %'] = 100.0 * v['fb_memory_usage']['used'] / v['fb_memory_usage']['total']
        return res