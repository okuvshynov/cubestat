import subprocess
from importlib.util import find_spec

from cubestat.common import GPUMode
from cubestat.metrics.base_metric import base_metric
from cubestat.metrics.registry import cubestat_metric

class gpu_metric(base_metric):
    def pre(self, mode, title):
        if self.n_gpus > 0 and mode == GPUMode.collapsed and "Total GPU" not in title:
            return False, ''
        if mode == GPUMode.load_only and "vram" in title:
            return False, ''
        if self.n_gpus > 1 and "Total GPU" not in title:
            return True, '  '
        return True, ''
    
    def format(self, values, idxs):
        return 100.0, [f'{values[i]:3.0f}%' for i in idxs]

    @classmethod
    def key(cls):
        return 'gpu'

@cubestat_metric
class nvidia_gpu_metric(gpu_metric):
    def __init__(self) -> None:
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

    def read(self, _context):
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

    @classmethod
    def supported_platforms(cls):
        return ['linux']
    
@cubestat_metric
class macos_gpu_metric(gpu_metric):
    def read(self, context):
        res = {}
        self.n_gpus = 1
        res['GPU util %'] = 100.0 - 100.0 * context['gpu']['idle_ratio']
        return res
    
    @classmethod
    def supported_platforms(cls):
        return ['macos']
