from cubestat.metrics_registry import cubestat_metric, collector_registry, presenter_registry
from cubestat.metrics.metric_adapter import MetricAdapter


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
