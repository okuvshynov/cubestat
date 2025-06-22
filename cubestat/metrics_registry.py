import importlib
import pkgutil
import sys

_metrics = []


class CollectorRegistry:
    def __init__(self):
        self._collectors = {}
    
    def register(self, platform):
        def decorator(cls):
            collector_id = cls.collector_id()
            if collector_id not in self._collectors:
                self._collectors[collector_id] = {}
            self._collectors[collector_id][platform] = cls
            return cls
        return decorator
    
    def get_collector(self, collector_id, platform):
        if collector_id in self._collectors:
            # Try exact platform match first
            if platform in self._collectors[collector_id]:
                return self._collectors[collector_id][platform]
            # Try platform prefix match
            for plat, cls in self._collectors[collector_id].items():
                if platform.startswith(plat):
                    return cls
        return None
    
    def get_instance(self, platform, collector_id):
        collector_cls = self.get_collector(collector_id, platform)
        return collector_cls() if collector_cls else None


collector_registry = CollectorRegistry()


class PresenterRegistry:
    def __init__(self):
        self._presenters = {}
    
    def register(self, presenter_cls):
        key = presenter_cls.key()
        self._presenters[key] = presenter_cls
        return presenter_cls
    
    def get(self, key):
        return self._presenters.get(key)
    
    def get_instance(self, key):
        presenter_cls = self._presenters.get(key)
        return presenter_cls() if presenter_cls else None


presenter_registry = PresenterRegistry()


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

# Import collectors and presenters
import_submodules("cubestat.collectors")
import_submodules("cubestat.presenters")
