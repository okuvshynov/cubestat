_metrics = []

def cubestat_metric(metric_class):
    key = metric_class.key()
    _metrics.append((key, metric_class))
    return metric_class

def get_metrics(platform, config):
    return {
        key: metric_class().configure(config)
        for key, metric_class in _metrics
        if platform in metric_class.supported_platforms()
    }
