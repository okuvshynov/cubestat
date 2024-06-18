from cubestat.common import PowerMode, label10

class power_metric:
    def __init__(self, platform) -> None:
        if platform == 'linux':
            self.read = self.read_linux
        if platform == 'macos':
            self.read = self.read_macos

    def read_macos(self, context):
        res = {}
        res['total power'] = context['processor']['combined_power']
        res['ANE power']   = context['processor']['ane_power']
        res['CPU power']   = context['processor']['cpu_power']
        res['GPU power']   = context['processor']['gpu_power']
        return res
    
    def read_linux(self, _context):
        return {}
    
    def pre(self, mode, title):
        if mode == PowerMode.off:
            return False, ''
        if mode == PowerMode.combined and 'total' not in title:
            return False, ''
        if 'total' not in title:
            return True, '  '
        return True, ''

    def format(self, values, idxs):
        return label10(values, [(1000 * 1000, 'kW'), (1000, 'W'), (1, 'mW')], idxs)