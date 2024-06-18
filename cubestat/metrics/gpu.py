import subprocess
from importlib.util import find_spec

from cubestat.common import GPUMode

class gpu_metric:
    def __init__(self, platform) -> None:
        if platform == 'linux':
            self.read = self.read_linux
        if platform == 'macos':
            self.read = self.read_macos
        self.has_nvidia = False
        self.n_gpus     = 0
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

    def read_macos(self, context):
        res = {}
        self.n_gpus = 1
        res['GPU util %'] = 100.0 - 100.0 * context['gpu']['idle_ratio']
        return res
    
    def read_linux(self, _context):
        res = {}
        total = 0
        if self.has_nvidia:
            self.n_gpus = 0
            for i, v in enumerate(self.nvsmi.DeviceQuery('utilization.gpu,memory.total,memory.used')['gpu']):
                res[f'GPU {i} util %'] = v['utilization']['gpu_util']
                total += v['utilization']['gpu_util']
                res[f'GPU {i} vram used %'] = 100.0 * v['fb_memory_usage']['used'] / v['fb_memory_usage']['total']
                self.n_gpus += 1
            if self.n_gpus > 1:
                combined = {}
                combined[f'[{self.n_gpus}] Total GPU util %'] = total / self.n_gpus
                for k, v in res.items():
                    combined[k] = v
                return combined
        return res
    
    def pre(self, mode, title):
        if self.n_gpus > 0 and mode == GPUMode.collapsed and "Total GPU" not in title:
            return False, ''
        if mode == GPUMode.load_only and "vram" in title:
            return False, ''
        if self.n_gpus > 1 and "Total GPU" not in title:
            return True, '  '
        return True, ''