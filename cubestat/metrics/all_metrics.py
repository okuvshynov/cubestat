"""Unified metric implementations using generic factory.

This module replaces all individual metric files with a configuration-driven approach.
All metrics are created using the generic factory functions.
"""

from cubestat.metrics.generic_metric import (
    create_cross_platform_metric,
    create_macos_only_metric
)

# Cross-platform metrics (available on both macOS and Linux)
CROSS_PLATFORM_METRICS = {
    "cpu": {
        "adapter_docstring": "CPU metric adapter handling hierarchical per-core and cluster data.",
        "platforms": {
            "darwin": {
                "class_name": "macos_cpu_metric",
                "docstring": "macOS CPU metric using new collector/presenter architecture."
            },
            "linux": {
                "class_name": "psutil_cpu_metric", 
                "docstring": "Linux CPU metric using new collector/presenter architecture."
            }
        }
    },
    "ram": {
        "adapter_docstring": "Memory metric adapter handling system and process memory data.",
        "platforms": {
            "darwin": {
                "collector_platform": "memory",
                "presenter_key": "memory",
                "class_name": "macos_memory_metric",
                "docstring": "macOS memory metric using new collector/presenter architecture."
            },
            "linux": {
                "collector_platform": "memory",
                "presenter_key": "memory",
                "class_name": "psutil_memory_metric",
                "docstring": "Linux memory metric using new collector/presenter architecture."
            }
        }
    },
    "network": {
        "adapter_docstring": "Network metric adapter handling data processing.",
        "platforms": {
            "darwin": {
                "class_name": "macos_network_metric",
                "docstring": "macOS network metric using new collector/presenter architecture."
            },
            "linux": {
                "class_name": "linux_network_metric",
                "docstring": "Linux network metric using new collector/presenter architecture."
            }
        }
    },
    "gpu": {
        "adapter_docstring": "GPU metric adapter handling multi-vendor GPU data.",
        "platforms": {
            "darwin": {
                "class_name": "macos_gpu_metric",
                "docstring": "macOS GPU metric using new collector/presenter architecture."
            },
            "linux": {
                "class_name": "linux_gpu_metric",
                "docstring": "Linux GPU metric using new collector/presenter architecture."
            }
        }
    },
    "disk": {
        "adapter_docstring": "Disk metric adapter for handling storage device metrics.",
        "platforms": {
            "darwin": {
                "class_name": "macos_disk_metric",
                "docstring": "macOS disk metric using new collector/presenter architecture."
            },
            "linux": {
                "class_name": "linux_disk_metric",
                "docstring": "Linux disk metric using new collector/presenter architecture."
            }
        }
    },
    "swap": {
        "adapter_docstring": "Swap metric adapter handling swap memory usage data.",
        "platforms": {
            "darwin": {
                "class_name": "macos_swap_metric",
                "docstring": "macOS swap metric using new collector/presenter architecture."
            },
            "linux": {
                "class_name": "psutil_swap_metric",
                "docstring": "Linux swap metric using new collector/presenter architecture."
            }
        }
    },
    "mock": {
        "adapter_docstring": "Mock metric adapter for testing purposes.",
        "platforms": {
            "darwin": {
                "collector_platform": "mock",
                "class_name": "mock_metric",
                "docstring": "macOS mock metric using new collector/presenter architecture."
            },
            "linux": {
                "collector_platform": "mock", 
                "class_name": "mock_metric",
                "docstring": "Linux mock metric using new collector/presenter architecture."
            }
        }
    }
}

# macOS-only metrics  
MACOS_ONLY_METRICS = {
    "power": {
        "adapter_docstring": "Power metric adapter handling energy consumption data.",
        "class_name": "macos_power_metric",
        "docstring": "macOS implementation of power metric using IOKit for energy monitoring."
    },
    "ane": {
        "adapter_docstring": "Apple Neural Engine metric adapter handling ML accelerator usage.",
        "collector_platform": "accel",
        "presenter_key": "accel",
        "class_name": "macos_ane_metric", 
        "docstring": "macOS implementation of ANE metric using IOKit for neural engine monitoring."
    }
}

# Create all cross-platform metric implementations
for metric_key, config in CROSS_PLATFORM_METRICS.items():
    create_cross_platform_metric(
        metric_key=metric_key,
        adapter_docstring=config["adapter_docstring"],
        platforms=config["platforms"]
    )

# Create macOS-only metric implementations
for metric_key, config in MACOS_ONLY_METRICS.items():
    create_macos_only_metric(
        metric_key=metric_key,
        adapter_docstring=config["adapter_docstring"],
        collector_platform=config.get("collector_platform"),
        presenter_key=config.get("presenter_key"),
        class_name=config["class_name"],
        docstring=config["docstring"]
    )