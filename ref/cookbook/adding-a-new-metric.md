# Adding a New Metric

This tutorial shows how to add a new metric to cubestat. We'll create a metric that monitors a specific aspect of system performance.

## Step 1: Create a new metric file

Create a new file in the `cubestat/metrics/` directory. For example, `temperature.py` for a CPU temperature metric:

```python
from cubestat.metrics.base_metric import base_metric
from cubestat.metrics_registry import cubestat_metric
from enum import Enum
import logging

class TempMode(Enum):
    show = "show"
    hide = "hide"
    
    def __str__(self):
        return self.value

@cubestat_metric(['linux', 'darwin'])  # Register for both Linux and macOS
class temperature_metric(base_metric):
    """Metric for monitoring CPU temperature."""
    
    def __init__(self) -> None:
        """Initialize the temperature metric."""
        self.mode = TempMode.show
    
    def read(self, context):
        """Read temperature data from the system.
        
        Args:
            context: Context dictionary containing system data
            
        Returns:
            Dictionary mapping component names to temperature values
        """
        result = {}
        try:
            # Implementation varies by platform - this would be filled in
            # with platform-specific code for reading temperatures
            # For example, using psutil or parsing system files
            result['CPU temperature °C'] = 50.0  # Example placeholder value
        except Exception as e:
            logging.warning(f"Failed to read temperature: {str(e)}")
        
        return result
    
    def format(self, title, values, idxs):
        """Format temperature values for display.
        
        Args:
            title: The metric title
            values: The temperature values
            idxs: Indices to format
            
        Returns:
            Tuple of (max_value, formatted_values)
        """
        # Assume 100°C as maximum safe temperature
        return 100.0, [f'{values[i]:.1f}°C' for i in idxs]
    
    def pre(self, title):
        """Determine if this metric should be displayed.
        
        Args:
            title: The metric title
            
        Returns:
            Tuple of (show_metric, indentation_level)
        """
        return self.mode == TempMode.show, 0
    
    def configure(self, conf):
        """Configure the temperature metric.
        
        Args:
            conf: Configuration object with command line arguments
            
        Returns:
            The configured metric instance
        """
        if hasattr(conf, 'temp'):
            self.mode = conf.temp
        return self
    
    @classmethod
    def key(cls):
        """Return the key that identifies this metric."""
        return 'temp'
    
    def hotkey(self):
        """Return the hotkey used to toggle this metric's display mode."""
        return 't'
    
    @classmethod
    def configure_argparse(cls, parser):
        """Configure command line arguments for this metric.
        
        Args:
            parser: The argument parser to configure
        """
        parser.add_argument(
            '--temp',
            type=TempMode,
            default=TempMode.show,
            choices=list(TempMode),
            help='Show CPU temperature. Can be toggled by pressing t.'
        )
```

## Step 2: Implement platform-specific code

For Linux, you might read temperatures from the system:

```python
@cubestat_metric('linux')
class linux_temperature_metric(temperature_metric):
    def read(self, context):
        result = {}
        try:
            # Read from /sys/class/thermal/
            with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                temp = float(f.read().strip()) / 1000.0  # Convert from millidegrees
                result['CPU temperature °C'] = temp
        except Exception as e:
            logging.warning(f"Failed to read Linux temperature: {str(e)}")
        
        return result
```

For macOS, you might use SMC commands:

```python
@cubestat_metric('darwin')
class macos_temperature_metric(temperature_metric):
    def read(self, context):
        result = {}
        try:
            # If powermetrics provides temperature data
            if 'powermetrics' in context and 'temperature' in context['powermetrics']:
                temp = context['powermetrics']['temperature']
                result['CPU temperature °C'] = temp
        except Exception as e:
            logging.warning(f"Failed to read macOS temperature: {str(e)}")
        
        return result
```

## Step 3: Register the metric

Metrics are automatically registered through the `@cubestat_metric` decorator. The decorator takes a platform name or list of platforms where the metric should be active.

## Step 4: Test your metric

Run cubestat to ensure your new metric displays correctly:

```bash
pip install -e .
cubestat
```

Press 't' to toggle the temperature display.

## Tips & Best Practices

- Always handle exceptions gracefully, using appropriate logging
- Implement platform-specific subclasses for different operating systems
- Choose a distinctive hotkey for toggling display modes
- Document your metric's functionality with proper docstrings
- Add unit tests for your metric in the `cubestat/tests/` directory
- When developing, use `--debug` flag for more verbose output

## Common Challenges

### Reading hardware sensors

Different platforms have different ways of exposing hardware sensor data:
- Linux: Check `/sys/class/thermal/`, `/proc/`, or use `lm-sensors`
- macOS: The `powermetrics` command provides hardware data, but requires root access
- For cross-platform support, consider using the `psutil` library

### Handling missing data

Sometimes sensor data may not be available. Handle this gracefully:

```python
def read(self, context):
    result = {}
    try:
        # Try to read the sensor
        temp = read_sensor()
        if temp is not None:
            result['CPU temperature °C'] = temp
    except Exception as e:
        logging.warning(f"Failed to read temperature: {str(e)}")
    
    # Return an empty dict if no data was read
    return result
```

### Displaying multiple values

If your metric returns multiple values (e.g., temperatures for different CPU cores):

```python
def read(self, context):
    result = {}
    try:
        # Read temperatures for multiple cores
        for i in range(4):  # Assuming 4 cores
            with open(f'/sys/class/thermal/thermal_zone{i}/temp', 'r') as f:
                temp = float(f.read().strip()) / 1000.0
                result[f'Core {i} temp °C'] = temp
    except Exception as e:
        logging.warning(f"Failed to read temperatures: {str(e)}")
    
    return result
```

## Next Steps

- [Implementing Platform-Specific Code](./implementing-platform-specific-code.md)
- [Adding Type Hints](./adding-type-hints.md)
- [Creating Unit Tests](./creating-unit-tests.md)