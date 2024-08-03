from cubestat.common import DisplayMode, label10
from cubestat.metrics.base_metric import base_metric
from cubestat.metrics_registry import cubestat_metric


class PowerMode(DisplayMode):
    combined = 'combined'
    all = 'all'
    off = 'off'


@cubestat_metric('darwin')
class macos_power_metric(base_metric):
    def read(self, context):
        res = {}
        res['total power'] = context['processor']['combined_power']
        res['ANE power'] = context['processor']['ane_power']
        res['CPU power'] = context['processor']['cpu_power']
        res['GPU power'] = context['processor']['gpu_power']
        return res

    def pre(self, title):
        if self.mode == PowerMode.off:
            return False, ''
        if self.mode == PowerMode.combined and 'total' not in title:
            return False, ''
        if 'total' not in title:
            return True, '  '
        return True, ''

    def configure(self, conf):
        self.mode = conf.power
        return self

    def format(self, title, values, idxs):
        return label10(values, [(1000 * 1000, 'kW'), (1000, 'W'), (1, 'mW')], idxs)

    @classmethod
    def key(cls):
        return 'power'

    def hotkey(self):
        return 'p'

    @classmethod
    def configure_argparse(cls, parser):
        parser.add_argument(
            '--power',
            type=PowerMode,
            default=PowerMode.combined,
            choices=list(PowerMode),
            help='Power: hidden, CPU/GPU/ANE breakdown, or combined usage. Hotkey: "p"'
        )
