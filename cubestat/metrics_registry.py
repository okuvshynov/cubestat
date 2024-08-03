import importlib
import pkgutil
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


def get_metrics(args):
    return {
        key: cls().configure(args)
        for key, cls in _metrics
    }


# Dynamically discover and import metrics
def import_submodules(package_name):
    package = importlib.import_module(package_name)
    for _, module_name, is_pkg in pkgutil.iter_modules(package.__path__):
        full_module_name = f"{package_name}.{module_name}"
        importlib.import_module(full_module_name)
        if is_pkg:
            import_submodules(full_module_name)


# Import all submodules of cubestat.metrics
import_submodules("cubestat.metrics")
