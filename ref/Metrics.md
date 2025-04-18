# Metrics

Cubestat supports various system metrics that are displayed as horizon charts. This document details the available metrics, their implementation, and functionality.

## Metrics System Overview

The metrics system in Cubestat follows a plugin-like architecture:

1. Each metric extends the `BaseMetric` class
2. Metrics are registered using the `cubestat_metric` decorator
3. The metrics registry dynamically loads all registered metrics
4. Each metric implements platform-specific data collection methods
5. Metrics can be configured via command-line arguments

## BaseMetric (base_metric.py)

The `BaseMetric` class provides the foundation for all metrics:

- **Abstract Methods**: Defines methods that all metrics must implement
- **Default Implementations**: Provides sensible defaults for common functionality
- **Configuration Interface**: Standardizes metric configuration

Key methods:
- `read(context)`: Read metric values from the system
- `format(title, values, indices)`: Format metric values for display
- `pre(title)`: Determine if and how a metric should be displayed
- `configure_argparse(parser)`: Add metric-specific command-line arguments

## Available Metrics

### CPU Metrics (cpu.py)

Measures CPU utilization across cores:

- **Modes**: All cores, by cluster, or by individual core
- **Implementation**: Uses psutil on Linux and powermetrics on macOS
- **Display**: Shows percentage utilization from 0-100%
- **Toggle**: Can be toggled with the 'c' key

Features:
- Core grouping for multi-cluster CPUs (e.g., Apple M-series)
- Per-core utilization tracking
- Configurable display modes

### GPU Metrics (gpu.py)

Monitors GPU utilization and memory:

- **Platforms**: Supports NVIDIA GPUs on Linux and integrated GPUs on macOS
- **Measurements**: Shows utilization percentage and VRAM usage
- **Implementation**: Uses nvidia-smi on Linux and powermetrics on macOS
- **Toggle**: Can be toggled with the 'g' key

Features:
- Multi-GPU support
- VRAM usage tracking (when available)
- Configurable display modes (load only, load and memory)

### Memory Metrics (memory.py)

Tracks system memory usage:

- **Measurements**: Shows percentage of used memory
- **Implementation**: Uses psutil on macOS and parses /proc/meminfo on Linux
- **Display**: Shows percentage utilization from 0-100%

Features:
- Physical memory tracking
- Detailed memory breakdown (when available)

### Disk Metrics (disk.py)

Monitors disk I/O activity:

- **Measurements**: Tracks read and write rates
- **Implementation**: Uses psutil for cross-platform support
- **Display**: Shows I/O rates with appropriate units (KB/s, MB/s, GB/s)
- **Toggle**: Can be toggled with the 'd' key

Features:
- Separate tracking for reads and writes
- Automatic unit scaling

### Network Metrics (network.py)

Tracks network I/O:

- **Measurements**: Monitors upload and download rates
- **Implementation**: Uses platform-specific methods to get network statistics
- **Display**: Shows rates with appropriate units (KB/s, MB/s, GB/s)
- **Toggle**: Can be toggled with the 'n' key

Features:
- Separate tracking for upload and download
- Automatic unit scaling

### Swap Metrics (swap.py)

Monitors swap memory usage:

- **Measurements**: Shows swap usage in absolute terms
- **Implementation**: Uses platform-specific methods (sysctl on macOS, /proc/meminfo on Linux)
- **Display**: Shows usage with appropriate units (KB, MB, GB)
- **Toggle**: Can be toggled with the 's' key

Features:
- Absolute value display
- Automatic unit scaling

### Power Metrics (power.py)

Tracks power consumption (macOS only):

- **Measurements**: Shows power usage for different components
- **Implementation**: Uses powermetrics on macOS
- **Display**: Shows power usage as percentage of maximum
- **Toggle**: Can be toggled with the 'p' key

Features:
- Component-specific power tracking
- Combined power mode option

### Accelerator Metrics (accel.py)

Monitors Apple Neural Engine utilization (macOS only):

- **Measurements**: Shows ANE utilization based on power consumption
- **Implementation**: Uses powermetrics on macOS
- **Display**: Shows utilization as percentage

Features:
- Support for different Apple Silicon models
- Power-based utilization estimate

### Mock Metrics (mock.py)

Provides a test metric implementation:

- **Purpose**: Used for development and testing
- **Implementation**: Simple incrementing counter
- **Display**: Shows test values

## Extending Metrics

To add a new metric to Cubestat:

1. Create a new Python file in the `metrics` directory
2. Inherit from `BaseMetric`
3. Implement required methods (read, format, pre)
4. Register with the `cubestat_metric` decorator
5. Add configuration options as needed

Example template for a new metric:

```python
from cubestat.metrics.base_metric import BaseMetric
from cubestat.metrics_registry import cubestat_metric

@cubestat_metric('my_metric')
class MyMetric(BaseMetric):
    def __init__(self, args):
        super().__init__(args)
        # Initialize metric-specific state
        
    def read(self, context):
        # Collect and return metric data
        return {'my_value': 42}
        
    def format(self, title, values, indices):
        # Format values for display
        max_value = max(values) if values else 0
        return max_value, [f"{values[i]:.2f}" for i in indices]
        
    def pre(self, title):
        # Determine display status
        return True, 0  # show=True, indent=0
        
    @staticmethod
    def configure_argparse(parser):
        # Add command-line arguments
        parser.add_argument('--my-option', type=str, default='default',
                           help='Description of my option')
```