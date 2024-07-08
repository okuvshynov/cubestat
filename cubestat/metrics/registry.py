import sys

_metrics = []

def cubestat_metric(*args):
    def decorator(cls):
        if any(sys.platform.startswith(platform) for platform in args):
            key = cls.key()
            _metrics.append((key, cls))
        return cls
    return decorator

def metrics_configure_argparse(parser):
    for _, metric_cls in _metrics:
        metric_cls.configure_argparse(parser)

def get_metrics(config):
    return {
        key: cls().configure(config)
        for key, cls in _metrics
    }

