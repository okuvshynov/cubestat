_metrics = []

def cubestat_metric(*args):
    def decorator(cls):
        cls.platforms = args
        key = cls.key()
        _metrics.append((key, cls))
        return cls
    return decorator

def get_metrics(platform, config):
    return {
        key: metric_class().configure(config)
        for key, metric_class in _metrics
        if platform in metric_class.platforms
    }
