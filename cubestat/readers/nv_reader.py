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
        total = 0
        if self.has_nvidia:
            n_gpus = 0
            for i, v in enumerate(self.nvsmi.DeviceQuery('utilization.gpu,memory.total,memory.used')['gpu']):
                res[f'GPU {i} util %'] = v['utilization']['gpu_util']
                total += v['utilization']['gpu_util']
                res[f'GPU {i} vram used %'] = 100.0 * v['fb_memory_usage']['used'] / v['fb_memory_usage']['total']
                n_gpus += 1
        if n_gpus > 1:
            combined = {}
            combined[f'[{n_gpus}] Total GPU util %'] = total / n_gpus
            for k, v in res.items():
                combined[k] = v
            return combined
        return res