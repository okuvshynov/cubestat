"""Simple metric factory functions.

This module provides factory functions to create Metric instances for different platforms.
"""

from typing import Type

from cubestat.metrics.metric import Metric
from cubestat.metrics_registry import collector_registry, presenter_registry, cubestat_metric


def create_metric(
    key: str,
    platform: str,
    collector_id: str = None,
    presenter_key: str = None
) -> Type[Metric]:
    """Create a metric class for a specific platform.
    
    Args:
        key: The metric key (e.g., "cpu", "ram")
        platform: Platform name (e.g., "darwin", "linux") 
        collector_id: Collector identifier (defaults to key)
        presenter_key: Presenter key (defaults to key)
        
    Returns:
        Metric class registered for the platform
    """
    collector_id = collector_id or key
    presenter_key = presenter_key or key
    
    @cubestat_metric(platform)
    class PlatformMetric(Metric):
        def __init__(self):
            collector = collector_registry.get_instance(platform, collector_id)
            presenter = presenter_registry.get_instance(presenter_key)
            super().__init__(key, collector, presenter)
        
        @classmethod
        def key(cls) -> str:
            return key
        
        @classmethod
        def configure_argparse(cls, parser):
            presenter_cls = presenter_registry.get(presenter_key)
            if presenter_cls:
                presenter_cls.configure_argparse(parser)
    
    # Set meaningful class name
    platform_name = "macos" if platform == "darwin" else platform
    PlatformMetric.__name__ = f"{platform_name}_{key}_metric"
    PlatformMetric.__qualname__ = PlatformMetric.__name__
    
    return PlatformMetric


def create_cross_platform_metric(
    key: str,
    darwin_collector_id: str = None,
    linux_collector_id: str = None,
    presenter_key: str = None
) -> dict:
    """Create metric implementations for both Darwin and Linux.
    
    Args:
        key: The metric key
        darwin_collector_id: Darwin collector ID (defaults to key)
        linux_collector_id: Linux collector ID (defaults to key) 
        presenter_key: Presenter key (defaults to key)
        
    Returns:
        Dictionary mapping platform to metric class
    """
    darwin_collector = darwin_collector_id or key
    linux_collector = linux_collector_id or key
    
    return {
        "darwin": create_metric(key, "darwin", darwin_collector, presenter_key),
        "linux": create_metric(key, "linux", linux_collector, presenter_key)
    }


def create_macos_only_metric(
    key: str,
    collector_id: str = None,
    presenter_key: str = None
) -> Type[Metric]:
    """Create a macOS-only metric implementation.
    
    Args:
        key: The metric key
        collector_id: Collector ID (defaults to key)
        presenter_key: Presenter key (defaults to key)
        
    Returns:
        macOS metric class
    """
    return create_metric(key, "darwin", collector_id, presenter_key)