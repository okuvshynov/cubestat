"""Unified metric implementations using simplified factory.

This module replaces all individual metric files with a simple factory-based approach.
All metrics are created using the simple factory functions.
"""

from cubestat.metrics.metric_factory import (
    create_cross_platform_metric,
    create_macos_only_metric
)

# Cross-platform metrics (available on both macOS and Linux)
CROSS_PLATFORM_METRICS = [
    "cpu",
    "network", 
    "gpu",
    "disk",
    "swap",
]

# Metrics with special collector/presenter mappings
SPECIAL_METRICS = {
    "ram": {
        "darwin_collector_id": "memory",
        "linux_collector_id": "memory", 
        "presenter_key": "memory"
    },
    "mock": {
        "darwin_collector_id": "mock",
        "linux_collector_id": "mock"
    }
}

# macOS-only metrics  
MACOS_ONLY_METRICS = {
    "power": {},
    "ane": {
        "collector_id": "accel",
        "presenter_key": "accel"
    }
}

# Create standard cross-platform metrics
for metric_key in CROSS_PLATFORM_METRICS:
    create_cross_platform_metric(metric_key)

# Create cross-platform metrics with special mappings
for metric_key, config in SPECIAL_METRICS.items():
    create_cross_platform_metric(
        key=metric_key,
        darwin_collector_id=config.get("darwin_collector_id"),
        linux_collector_id=config.get("linux_collector_id"),
        presenter_key=config.get("presenter_key")
    )

# Create macOS-only metric implementations
for metric_key, config in MACOS_ONLY_METRICS.items():
    create_macos_only_metric(
        key=metric_key,
        collector_id=config.get("collector_id"),
        presenter_key=config.get("presenter_key")
    )