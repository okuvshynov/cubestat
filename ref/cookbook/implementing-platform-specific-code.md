# Implementing Platform-Specific Code

This tutorial demonstrates how to implement platform-specific functionality in cubestat.

## Step 1: Update the platform factory

First, ensure the platform factory can detect the new platform. Modify `platforms/factory.py`:

```python
def get_platform(interval_ms):
    """Create and return the appropriate platform implementation."""
    system = platform.system()
    if system == 'Darwin':
        return MacOSPlatform(interval_ms)
    elif system == 'Linux':
        return LinuxPlatform(interval_ms)
    elif system == 'Windows':  # New platform
        return WindowsPlatform(interval_ms)
    else:
        raise RuntimeError(f"Unsupported platform: {system}")
```

## Step 2: Create the platform implementation

Create a new file in the `platforms` directory, e.g., `windows.py`:

```python
import time
import logging
import threading
import psutil

class WindowsPlatform:
    """Windows platform implementation for cubestat."""
    
    def __init__(self, interval_ms):
        """Initialize the Windows platform.
        
        Args:
            interval_ms: Refresh interval in milliseconds
        """
        self.interval_s = interval_ms / 1000.0
        self.running = False
        self.thread = None
    
    def loop(self, callback):
        """Run the data collection loop.
        
        Args:
            callback: Function to call with collected data
        """
        self.running = True
        
        def _loop():
            last_time = time.time()
            while self.running:
                try:
                    # Collect Windows-specific metrics
                    context = {
                        'timestamp': time.time(),
                        'windows': {
                            # Windows-specific data would go here
                            # For example, using psutil or WMI
                            'cpu': psutil.cpu_percent(percpu=True),
                            'memory': psutil.virtual_memory()._asdict(),
                        }
                    }
                    
                    # Call the callback with the collected data
                    callback(context)
                    
                    # Calculate sleep time to maintain the desired interval
                    now = time.time()
                    elapsed = now - last_time
                    sleep_time = max(0, self.interval_s - elapsed)
                    time.sleep(sleep_time)
                    last_time = now
                
                except Exception as e:
                    logging.error(f"Error in Windows platform loop: {str(e)}")
                    time.sleep(self.interval_s)  # Sleep and retry
        
        self.thread = threading.Thread(target=_loop)
        self.thread.daemon = True
        self.thread.start()
    
    def stop(self):
        """Stop the data collection loop."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2.0)  # Wait for thread to terminate

    def get_additional_context(self):
        """Return additional platform-specific context information.
        
        Returns:
            Dictionary with platform-specific context data
        """
        return {
            'platform': 'windows',
            'version': platform.version(),
            'release': platform.release(),
        }
```

## Step 3: Register platform-specific metrics

Add the platform specifier to your metrics:

```python
@cubestat_metric('windows')
class windows_cpu_metric(cpu_metric):
    # Windows-specific CPU metric implementation
    pass
```

## Step 4: Import the platform in factory.py

Update the imports in `platforms/factory.py`:

```python
from cubestat.platforms.linux import LinuxPlatform
from cubestat.platforms.macos import MacOSPlatform
from cubestat.platforms.windows import WindowsPlatform  # New import
```

## Step 5: Test on the target platform

To test your implementation:

```bash
pip install -e .
cubestat --debug
```

## Understanding the Platform Architecture

The platform architecture in cubestat follows these principles:

1. **Platform Detection**: The factory pattern detects the operating system and initializes the appropriate platform implementation.

2. **Data Collection Loop**: Each platform implementation runs a background thread that collects system data at regular intervals.

3. **Context Building**: The platform builds a context dictionary with system data, which is passed to metrics.

4. **Callback Mechanism**: The data collection loop calls a callback function when new data is available, which updates the display.

## Common Platform-Specific Data Sources

### Linux
- `/proc` filesystem for system information
- `/sys` filesystem for hardware information
- Commands like `lspci`, `lshw`, and `sensors`

### macOS
- `sysctl` for system parameters
- `powermetrics` for power and performance data (requires root)
- IOKit for device information

### Windows
- Windows Management Instrumentation (WMI)
- Performance counters
- Windows registry

## Best Practices

1. **Handle Permissions**: Some system data requires elevated permissions. Handle permission errors gracefully.

2. **Resource Efficiency**: Be mindful of performance; reading system data shouldn't consume excessive resources.

3. **Error Handling**: Always use try/except blocks and log errors appropriately.

4. **Caching**: Cache expensive operations to avoid repeated calls.

5. **Documentation**: Document all platform-specific details, including required permissions and dependencies.

## Example: Adding GPU Metrics for Windows

```python
@cubestat_metric('windows')
class windows_gpu_metric(gpu_metric):
    def read(self, context):
        result = {}
        try:
            # Using Windows-specific APIs like NVAPI or WMI for NVIDIA GPUs
            import wmi  # You might need to install this package
            computer = wmi.WMI()
            
            # Query GPU information
            gpu_info = computer.Win32_VideoController()
            
            for i, gpu in enumerate(gpu_info):
                result[f'GPU {i} Usage %'] = get_gpu_usage(gpu.DeviceID)
                result[f'GPU {i} Memory %'] = get_gpu_memory(gpu.DeviceID)
                
        except Exception as e:
            logging.warning(f"Failed to read Windows GPU metrics: {str(e)}")
        
        return result
    
    def get_gpu_usage(device_id):
        # Implementation for getting GPU usage
        pass
        
    def get_gpu_memory(device_id):
        # Implementation for getting GPU memory usage
        pass
```

## Next Steps

- [Adding a New Metric](./adding-a-new-metric.md)
- [Building Custom Visualizations](./building-custom-visualizations.md)
- [Cross-Platform Testing](./cross-platform-testing.md)