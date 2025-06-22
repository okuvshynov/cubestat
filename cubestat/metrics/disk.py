import sys
import psutil

from cubestat.common import SimpleMode, RateReader, label_bytes_per_sec
from cubestat.metrics.base_metric import base_metric
from cubestat.metrics_registry import cubestat_metric, collector_registry, presenter_registry
from cubestat.metrics.metric_adapter import MetricAdapter


class disk_metric(base_metric):
    def pre(self, title):
        if self.mode == SimpleMode.hide:
            return False, ''
        return True, ''

    def format(self, title, values, idxs):
        return label_bytes_per_sec(values, idxs)

    @classmethod
    def key(cls):
        return 'disk'

    def hotkey(self):
        return 'd'

    @classmethod
    def configure_argparse(cls, parser):
        parser.add_argument(
            '--disk',
            type=SimpleMode,
            default=SimpleMode.show,
            choices=list(SimpleMode),
            help='Show disk read/write rate. Hotkey: "d"'
        )

    def configure(self, conf):
        self.mode = conf.disk
        self.rate_reader = RateReader(conf.refresh_ms)
        return self


# Old implementations - commented out in favor of new collector/presenter architecture
# @cubestat_metric('darwin')
# class macos_disc_metric(disk_metric):
#     def read(self, context):
#         res = {}
#         res['disk read'] = context['disk']['rbytes_per_s']
#         res['disk write'] = context['disk']['wbytes_per_s']
#         return res
# 
# 
# @cubestat_metric('linux')
# class linux_disc_metric(disk_metric):
#     def read(self, _context):
#         res = {}
#         disk_io = psutil.disk_io_counters()
#         res['disk read'] = self.rate_reader.next('disk read', disk_io.read_bytes)
#         res['disk write'] = self.rate_reader.next('disk write', disk_io.write_bytes)
#         return res


# New refactored disk metric implementations
@cubestat_metric('darwin')
class MacOSDiskMetric(MetricAdapter):
    def __init__(self):
        collector_cls = collector_registry.get_collector('disk', 'darwin')
        presenter_cls = presenter_registry.get('disk')
        if not collector_cls or not presenter_cls:
            raise RuntimeError("Disk collector or presenter not found")
        super().__init__(collector_cls(), presenter_cls())
    
    @classmethod
    def key(cls):
        return 'disk'
    
    @classmethod
    def configure_argparse(cls, parser):
        # Delegate to presenter's configure_argparse
        presenter_cls = presenter_registry.get('disk')
        if presenter_cls:
            presenter_cls.configure_argparse(parser)


@cubestat_metric('linux')
class LinuxDiskMetric(MetricAdapter):
    def __init__(self):
        collector_cls = collector_registry.get_collector('disk', 'linux')
        presenter_cls = presenter_registry.get('disk')
        if not collector_cls or not presenter_cls:
            raise RuntimeError("Disk collector or presenter not found")
        super().__init__(collector_cls(), presenter_cls())
    
    @classmethod
    def key(cls):
        return 'disk'
    
    @classmethod
    def configure_argparse(cls, parser):
        # Delegate to presenter's configure_argparse
        presenter_cls = presenter_registry.get('disk')
        if presenter_cls:
            presenter_cls.configure_argparse(parser)
