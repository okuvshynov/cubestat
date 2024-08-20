from cubestat.metrics.base_metric import base_metric
from cubestat.metrics_registry import cubestat_metric

@cubestat_metric('darwin')
class mock_metric(base_metric):
    def read(self, context):
        res = {'mock': self.v}
        self.v += 1.0
        return res

    def pre(self, title):
        return False, ''
    
    def format(self, title, values, idxs):
        return 100.0, [f'{values[i]:3.0f}%' for i in idxs]

    @classmethod
    def key(cls):
        return 'mock'

    def hotkey(self):
        return 'w'

    @classmethod
    def configure_argparse(cls, parser):
        pass

    def configure(self, conf):
        self.v = 0.0
        return self

