"""Generic metric implementation factory.

This module provides a factory function to create metric implementations
following the standard pattern used across all metrics.
"""

from argparse import ArgumentParser
from typing import Type, Optional, Dict, Any

from cubestat.metrics.metric_adapter import MetricAdapter
from cubestat.metrics_registry import collector_registry, presenter_registry, cubestat_metric


def create_metric_adapter(metric_key: str, docstring: str = "") -> Type[MetricAdapter]:
    """Create a metric adapter class for a given metric key.
    
    Args:
        metric_key: The key identifying the metric (e.g., "cpu", "ram", "network")
        docstring: Optional docstring for the adapter class
        
    Returns:
        A MetricAdapter subclass configured for the given metric
    """
    
    class GenericMetricAdapter(MetricAdapter):
        __doc__ = docstring or f"{metric_key.upper()} metric adapter handling data flow between collector and presenter."
        
        @classmethod
        def key(cls) -> str:
            return metric_key
            
        @classmethod
        def configure_argparse(cls, parser: ArgumentParser) -> None:
            presenter_cls = presenter_registry.get(metric_key)
            if presenter_cls:
                presenter_cls.configure_argparse(parser)
    
    # Set a meaningful name for the class
    GenericMetricAdapter.__name__ = f"{metric_key.capitalize()}MetricAdapter"
    GenericMetricAdapter.__qualname__ = GenericMetricAdapter.__name__
    
    return GenericMetricAdapter


def create_platform_metric(
    adapter_class: Type[MetricAdapter],
    platform: str,
    metric_key: str,
    collector_platform: Optional[str] = None,
    presenter_key: Optional[str] = None,
    class_name: Optional[str] = None,
    docstring: Optional[str] = None
) -> Type[MetricAdapter]:
    """Create a platform-specific metric implementation.
    
    Args:
        adapter_class: The adapter class to inherit from
        platform: The platform this metric supports (e.g., "darwin", "linux")
        metric_key: The key identifying the metric
        collector_platform: The collector platform key (defaults to platform)
        class_name: Optional custom class name
        docstring: Optional docstring for the class
        
    Returns:
        A platform-specific metric implementation decorated with @cubestat_metric
    """
    # Use provided collector platform or default to platform
    if collector_platform is None:
        collector_platform = platform
    
    # Generate default class name if not provided
    if class_name is None:
        class_name = f"{platform}_{metric_key}_metric"
    
    # Generate default docstring if not provided
    if docstring is None:
        docstring = f"{platform.capitalize()} implementation of {metric_key} metric."
    
    @cubestat_metric(platform)
    class PlatformMetric(adapter_class):
        __doc__ = docstring
        
        def __init__(self):
            collector = collector_registry.get_instance(platform, collector_platform)
            presenter = presenter_registry.get_instance(presenter_key or metric_key)
            super().__init__(collector, presenter)
    
    # Set the class name
    PlatformMetric.__name__ = class_name
    PlatformMetric.__qualname__ = class_name
    
    return PlatformMetric


def create_cross_platform_metric(
    metric_key: str,
    adapter_docstring: str = "",
    platforms: Optional[Dict[str, Dict[str, Any]]] = None
) -> Dict[str, Type[MetricAdapter]]:
    """Create metric implementations for multiple platforms.
    
    Args:
        metric_key: The key identifying the metric
        adapter_docstring: Docstring for the adapter class
        platforms: Dict mapping platform to config dict with optional keys:
                  - collector_platform: collector platform key
                  - class_name: custom class name
                  - docstring: custom docstring
                  
    Returns:
        Dict mapping platform to metric implementation class
    """
    if platforms is None:
        # Default cross-platform configuration
        platforms = {
            "darwin": {
                "collector_platform": metric_key,
                "class_name": f"macos_{metric_key}_metric",
                "docstring": f"macOS implementation of {metric_key} metric using system-specific data collection."
            },
            "linux": {
                "collector_platform": metric_key,
                "class_name": f"linux_{metric_key}_metric", 
                "docstring": f"Linux implementation of {metric_key} metric using system-specific data collection."
            }
        }
    
    # Create the adapter class once
    adapter_class = create_metric_adapter(metric_key, adapter_docstring)
    
    # Create platform-specific implementations
    implementations = {}
    for platform, config in platforms.items():
        # Extract config with defaults
        collector_platform = config.get("collector_platform", metric_key)
        presenter_key = config.get("presenter_key", metric_key)
        class_name = config.get("class_name", f"{platform}_{metric_key}_metric")
        docstring = config.get("docstring", f"{platform.capitalize()} implementation of {metric_key} metric.")
        
        impl = create_platform_metric(
            adapter_class=adapter_class,
            platform=platform,
            metric_key=metric_key,
            collector_platform=collector_platform,
            presenter_key=presenter_key,
            class_name=class_name,
            docstring=docstring
        )
        
        implementations[platform] = impl
    
    return implementations


def create_macos_only_metric(
    metric_key: str,
    adapter_docstring: str = "",
    collector_platform: Optional[str] = None,
    presenter_key: Optional[str] = None,
    class_name: Optional[str] = None,
    docstring: Optional[str] = None
) -> Type[MetricAdapter]:
    """Create a macOS-only metric implementation.
    
    Args:
        metric_key: The key identifying the metric
        adapter_docstring: Docstring for the adapter class
        class_name: Optional custom class name
        docstring: Optional docstring for the implementation
        
    Returns:
        A macOS-only metric implementation
    """
    # Create the adapter class
    adapter_class = create_metric_adapter(metric_key, adapter_docstring)
    
    # Create macOS implementation
    return create_platform_metric(
        adapter_class=adapter_class,
        platform="darwin",
        metric_key=metric_key,
        collector_platform=collector_platform or metric_key,
        presenter_key=presenter_key,
        class_name=class_name or f"macos_{metric_key}_metric",
        docstring=docstring or f"macOS implementation of {metric_key} metric using IOKit for system monitoring."
    )