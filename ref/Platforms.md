# Platform Support

Cubestat is designed to work across different platforms, with specific implementations for each supported operating system. This document details the platform-specific implementations and their functionality.

## Platform Architecture

Cubestat uses a factory pattern to create the appropriate platform implementation:

1. The `get_platform` function in `platforms/factory.py` determines the current OS
2. It instantiates the relevant platform class (MacOSPlatform or LinuxPlatform)
3. Each platform implements a consistent interface for data collection
4. Platform-specific metrics are enabled based on the detected platform

## Platform Factory (factory.py)

The platform factory manages platform detection and instantiation:

- **Platform Detection**: Uses `platform.system()` to identify the current OS
- **Instance Creation**: Creates the appropriate platform implementation
- **Error Handling**: Raises an exception for unsupported platforms

Implementation:
```python
def get_platform(interval_ms):
    """
    Create and return the appropriate platform implementation
    based on the current operating system.
    """
    system = platform.system()
    if system == 'Darwin':
        return MacOSPlatform(interval_ms)
    elif system == 'Linux':
        return LinuxPlatform(interval_ms)
    else:
        raise RuntimeError(f"Unsupported platform: {system}")
```

## macOS Platform (macos.py)

The `MacOSPlatform` class provides macOS-specific functionality:

- **Data Collection**: Uses Apple's `powermetrics` command-line tool
- **Process Management**: Runs powermetrics as a subprocess with sudo
- **Data Parsing**: Parses plist XML output from powermetrics
- **Metrics Support**: Provides detailed GPU, CPU, ANE, and power metrics

Key features:
- Uses plistlib for XML parsing
- Handles authentication for powermetrics (requires sudo)
- Provides detailed M-series chip metrics
- Supports cluster-level CPU monitoring

Implementation details:
- Launches powermetrics with appropriate parameters
- Continuously reads from the process output
- Parses complete plist documents when available
- Calls the callback function with the parsed data

Limitations:
- Requires sudo access for powermetrics
- Only available on macOS
- Particularly optimized for Apple Silicon (M1/M2/M3)

## Linux Platform (linux.py)

The `LinuxPlatform` class provides Linux-specific functionality:

- **Data Collection**: Uses direct system file parsing (/proc, /sys)
- **Implementation**: Uses simple polling at specified intervals
- **Metrics Support**: Provides CPU, memory, disk, and network metrics
- **GPU Support**: Integrates with NVIDIA GPUs via pynvml when available

Key features:
- Lightweight polling implementation
- No external process dependencies
- Support for NVIDIA GPUs
- Simple timing-based metric collection

Implementation details:
- Uses a time-based polling mechanism
- Calls the callback function at regular intervals
- Provides a timestamp for metrics synchronization
- Uses efficient system file parsing

## Platform Interface

Both platform implementations share a common interface:

- **Initialization**: Takes a refresh interval parameter
- **Loop Method**: Implements a continuous data collection loop
- **Callback**: Calls a provided callback function with collected data
- **Context**: Provides platform-specific context data to metrics

## Platform-Specific Data Context

Each platform provides a different data context structure to metrics:

### macOS Context
```
{
    'timestamp': float,  # Current timestamp
    'powermetrics': {    # Raw powermetrics data
        'processor': {   # CPU-related data
            'clusters': [...],
            'cores': [...]
        },
        'gpu': {         # GPU-related data
            'control': {...},
            'engines': [...]
        },
        'network': {...}, # Network data
        'memory': {...},  # Memory data
        'ane': {...}      # Apple Neural Engine data
    }
}
```

### Linux Context
```
{
    'timestamp': float,  # Current timestamp
    # All other data is collected directly by metrics
}
```

## Cross-Platform Considerations

When developing for Cubestat, consider these cross-platform aspects:

1. **Metric Implementations**: Metrics must handle both platforms or gracefully degrade
2. **Feature Detection**: Check for platform-specific features before using them
3. **Error Handling**: Provide graceful fallbacks for unsupported features
4. **Data Normalization**: Ensure consistent data representation across platforms
5. **Performance Impact**: Consider the performance impact of each platform's implementation

## Adding New Platform Support

To add support for a new platform:

1. Create a new Python file in the `platforms` directory
2. Implement a platform class with the required interface (similar to existing platforms)
3. Update the factory function to detect and create the new platform
4. Ensure metrics can handle the new platform's context format
5. Test thoroughly on the new platform