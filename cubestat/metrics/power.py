from cubestat.common import PowerMode, label10
from cubestat.metrics.base_metric import base_metric
from cubestat.metrics.registry import cubestat_metric

@cubestat_metric('darwin')
class macos_power_metric(base_metric):
    def read(self, context):
        res = {}
        res['total power'] = context['processor']['combined_power']
        res['ANE power']   = context['processor']['ane_power']
        res['CPU power']   = context['processor']['cpu_power']
        res['GPU power']   = context['processor']['gpu_power']
        return res
    
    def pre(self, mode, title):
        if mode == PowerMode.off:
            return False, ''
        if mode == PowerMode.combined and 'total' not in title:
            return False, ''
        if 'total' not in title:
            return True, '  '
        return True, ''

    def configure(self, conf):
        self.mode = conf.power
        return self

    def format(self, values, idxs):
        return label10(values, [(1000 * 1000, 'kW'), (1000, 'W'), (1, 'mW')], idxs)

    @classmethod
    def key(cls):
        return 'power'

    def hotkey(self):
        return 'p'

    @classmethod
    def configure_argparse(cls, parser):
        parser.add_argument('--power', type=PowerMode, default=PowerMode.combined, choices=list(PowerMode), help='Power mode - off, showing breakdown CPU/GPU/ANE load, or showing combined usage. Can be toggled by pressing p.')
