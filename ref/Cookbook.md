# Cubestat Cookbook

This cookbook provides practical, tutorial-style guides for working with the cubestat codebase. Each recipe focuses on a specific task and guides you through implementation.

## Table of Contents

1. [Adding a New Metric](#adding-a-new-metric)
2. [Implementing Platform-Specific Code](#implementing-platform-specific-code)
3. [Adding Type Hints to Legacy Code](#adding-type-hints-to-legacy-code)
4. [Creating Unit Tests](#creating-unit-tests)
5. [Implementing Logging](#implementing-logging)
6. [Building a Custom Visualization](#building-a-custom-visualization)
7. [Creating a Load Generator](#creating-a-load-generator)

## Adding a New Metric

This recipe shows how to add a new metric to cubestat. We'll create a metric that monitors a specific aspect of system performance.

### Step 1: Create a new metric file

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

### Step 2: Implement platform-specific code

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

### Step 3: Test your metric

Run cubestat to ensure your new metric displays correctly:

```bash
pip install -e .
cubestat
```

Press 't' to toggle the temperature display.

## Implementing Platform-Specific Code

This recipe demonstrates how to implement platform-specific functionality in cubestat.

### Step 1: Update the platform detector

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

### Step 2: Create the platform implementation

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
```

### Step 3: Register platform-specific metrics

Add the platform specifier to your metrics:

```python
@cubestat_metric('windows')
class windows_cpu_metric(cpu_metric):
    # Windows-specific CPU metric implementation
    pass
```

## Adding Type Hints to Legacy Code

This recipe demonstrates how to add type hints to existing code in cubestat, following the modernization plan.

### Step 1: Set up type checking infrastructure

Ensure you have mypy configured properly:

```bash
pip install mypy
```

And verify the mypy.ini configuration file exists:

```ini
[mypy]
python_version = 3.8
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = false
disallow_incomplete_defs = false
check_untyped_defs = true
disallow_untyped_decorators = false
no_implicit_optional = true
strict_optional = true
```

### Step 2: Add imports and type variables

At the top of the file, add the necessary imports:

```python
from typing import Any, Dict, List, Optional, Sequence, Tuple, TypeVar, Union
```

If needed, define type variables for generic methods:

```python
T = TypeVar('T', bound='DisplayMode')
```

### Step 3: Add type hints to function signatures

For each function, add parameter and return type annotations:

```python
# Before
def format_measurement(curr, mx, buckets):
    # function implementation

# After
def format_measurement(curr: float, mx: float, buckets: List[Tuple[float, str]]) -> str:
    """Format a measurement value using appropriate unit buckets.
    
    Args:
        curr: Current value to format
        mx: Maximum value (used to determine appropriate unit)
        buckets: List of (factor, unit) tuples for conversion
        
    Returns:
        Formatted measurement string
    """
    # function implementation
```

### Step 4: Add class variable and attribute type hints

For classes, add type hints to attributes:

```python
# Before
class RateReader:
    def __init__(self, interval_ms):
        self.interval_s = interval_ms / 1000.0
        self.last = {}

# After
class RateReader:
    """Calculate rates from consecutive measurements."""
    
    interval_s: float
    last: Dict[str, float]
    
    def __init__(self, interval_ms: int) -> None:
        """Initialize a rate reader.
        
        Args:
            interval_ms: Interval between measurements in milliseconds
        """
        self.interval_s = interval_ms / 1000.0
        self.last = {}
```

### Step 5: Run the type checker

Verify your type hints with mypy:

```bash
mypy cubestat
```

Fix any type errors that are reported.

## Creating Unit Tests

This recipe demonstrates how to create unit tests for cubestat components.

### Step 1: Create a test file

Create a new file in the `cubestat/tests/` directory, for example, `test_your_module.py`:

```python
"""Tests for your module."""

import unittest
from cubestat.your_module import YourClass

class TestYourClass(unittest.TestCase):
    """Test cases for YourClass."""

    def setUp(self) -> None:
        """Set up the test environment."""
        self.test_instance = YourClass(param1=1, param2="test")
    
    def tearDown(self) -> None:
        """Clean up after the test."""
        # Clean up resources if needed
        pass
    
    def test_some_method(self) -> None:
        """Test that your method works correctly."""
        # Arrange
        expected_result = 42
        
        # Act
        actual_result = self.test_instance.some_method()
        
        # Assert
        self.assertEqual(expected_result, actual_result)
    
    def test_error_handling(self) -> None:
        """Test that errors are handled properly."""
        # Arrange - set up a state that will cause an error
        
        # Act & Assert - verify that the expected exception is raised
        with self.assertRaises(ValueError):
            self.test_instance.some_method_that_raises()
```

### Step 2: Run the tests

Run the tests to verify your implementation:

```bash
# Run all tests
python -m unittest discover

# Run just your test
python -m unittest cubestat.tests.test_your_module
```

### Example: Rate Reader Test

Here's a concrete example of testing the RateReader class:

```python
import unittest
from cubestat.common import RateReader

class TestRateReader(unittest.TestCase):
    """Test cases for the RateReader class."""

    def test_init(self) -> None:
        """Test initialization of RateReader."""
        interval_ms = 1000
        reader = RateReader(interval_ms)
        self.assertEqual(reader.interval_s, 1.0)
        self.assertEqual(reader.last, {})

    def test_next_first_call(self) -> None:
        """Test that first call to next returns 0."""
        interval_ms = 1000
        reader = RateReader(interval_ms)
        key = "test_key"
        value = 100.0
        rate = reader.next(key, value)
        
        self.assertEqual(rate, 0.0)
        self.assertEqual(reader.last[key], value)

    def test_next_positive_rate(self) -> None:
        """Test calculation of positive rate."""
        interval_ms = 1000
        reader = RateReader(interval_ms)
        key = "test_key"
        
        # First call initializes the value
        reader.next(key, 100.0)
        
        # Second call calculates the rate
        rate = reader.next(key, 200.0)
        
        # Rate should be (200 - 100) / 1.0 = 100.0 units per second
        self.assertEqual(rate, 100.0)
        self.assertEqual(reader.last[key], 200.0)
```

## Implementing Logging

This recipe shows how to implement proper logging in cubestat components.

### Step 1: Set up a logger

First, create or update the logging configuration in `cubestat/logging.py`:

```python
"""Logging configuration for cubestat."""

import logging
import os
import sys
from typing import Optional

def configure_logging(
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    console: bool = True
) -> None:
    """Configure logging for cubestat.
    
    Args:
        level: The logging level
        log_file: Path to log file, if None, logs are only sent to console
        console: Whether to log to console
    """
    logger = logging.getLogger("cubestat")
    logger.setLevel(level)
    logger.handlers = []  # Remove existing handlers
    
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Add file handler if log_file is specified
    if log_file:
        try:
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except (IOError, OSError) as e:
            print(f"Error setting up log file: {e}", file=sys.stderr)
    
    # Add console handler if requested
    if console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
```

### Step 2: Initialize logging in the application

In the application's initialization (e.g., `__init__.py`):

```python
"""Cubestat - Horizon chart in terminal for system monitoring."""

__version__ = "0.3.4"

from cubestat.logging import configure_logging

# Initialize default logging configuration
configure_logging()
```

### Step 3: Use logging in your code

Replace print statements and silent exception handling with proper logging:

```python
# Before
def init_gpu():
    try:
        subprocess.check_output('nvidia-smi')
        # GPU found
    except Exception:
        # No GPU found, do nothing
        pass

# After
import logging

logger = logging.getLogger("cubestat")

def init_gpu():
    try:
        subprocess.check_output(['nvidia-smi'], stderr=subprocess.PIPE)
        logger.info("NVIDIA GPU detected")
    except subprocess.CalledProcessError as e:
        logger.warning(f"nvidia-smi command failed: {e.stderr.decode() if e.stderr else 'unknown error'}")
    except FileNotFoundError:
        logger.warning("nvidia-smi not found, NVIDIA GPU monitoring disabled")
    except Exception as e:
        logger.exception(f"Unexpected error initializing GPU metrics: {str(e)}")
```

### Step 4: Configure log levels appropriately

Use appropriate log levels:

- `DEBUG`: Detailed information for debugging
- `INFO`: Confirmation that things are working
- `WARNING`: Something unexpected happened but the application can continue
- `ERROR`: Something failed but the application can still function
- `CRITICAL`: A serious error that may prevent the application from continuing

Example:

```python
def read_metrics(self, context):
    try:
        logger.debug("Reading metrics from context")
        # Implementation...
        logger.info("Successfully read metrics")
        return metrics
    except KeyError as e:
        logger.warning(f"Missing key in metrics data: {str(e)}")
        return {}
    except Exception as e:
        logger.error(f"Failed to read metrics: {str(e)}")
        return {}
```

## Building a Custom Visualization

This recipe shows how to create a custom visualization for cubestat metrics.

### Step 1: Understand the Screen rendering system

The Screen class in `cubestat/screen.py` handles the rendering of charts. It uses the curses library to draw in the terminal. Key methods:

- `render_start()`: Prepares the screen for rendering
- `render_ruler()`: Draws the ruler with metric labels
- `render_chart()`: Draws the horizon chart for a metric
- `render_done()`: Finalizes rendering

### Step 2: Create a new visualization method

Add a new method to the Screen class:

```python
def render_sparkline(self, colors, max_value, values, row):
    """Render a sparkline visualization of values.
    
    Args:
        colors: Color scheme to use
        max_value: Maximum value for scaling
        values: List of values to render
        row: Row position to render at
    """
    if not values:
        return
    
    # Calculate display width based on terminal size
    chart_width = min(len(values), self.cols)
    
    # Prepare the sparkline character set (lower to higher)
    # Using Unicode block characters for the sparkline
    spark_chars = [' ', '▁', '▂', '▃', '▄', '▅', '▆', '▇', '█']
    
    # Render each value as a sparkline character
    for i, value in enumerate(values[-chart_width:]):
        if i >= self.cols:
            break
            
        # Scale the value to the sparkline character range
        if max_value > 0:
            norm_value = min(1.0, max(0.0, value / max_value))
            char_index = min(len(spark_chars) - 1, 
                             int(norm_value * (len(spark_chars) - 1)))
            char = spark_chars[char_index]
        else:
            char = spark_chars[0]
        
        # Choose color based on value intensity
        color_idx = min(len(colors) - 1, 
                        int(norm_value * len(colors)))
        color = colors[color_idx]
        
        # Set color and draw the character
        self.stdscr.attron(curses.color_pair(color))
        self.stdscr.addstr(row, i, char)
        self.stdscr.attroff(curses.color_pair(color))
```

### Step 3: Update Cubestat to use the new visualization

Modify the Cubestat class to support the new visualization:

```python
# Add a new mode to ViewMode
class ViewMode(DisplayMode):
    off = "off"
    one = "one"
    all = "all"
    sparkline = "sparkline"  # New visualization mode

# Update the render method to use the new visualization
def render(self) -> None:
    # ... existing code ...
    
    if self.view == ViewMode.sparkline:
        # Use sparkline visualization
        self.screen.render_sparkline(theme, max_value, data_slice, row)
    else:
        # Use horizon chart (existing)
        self.screen.render_chart(theme, max_value, data_slice, row)
    
    # ... rest of existing code ...
```

### Step 4: Add a keyboard shortcut to toggle the visualization

Update the InputHandler to support toggling the visualization:

```python
def handle_input(self):
    # ... existing code ...
    
    elif c == ord('y'):  # 'y' toggles visualization mode
        self.app.view = self.app.view.next()
        self.app.settings_changed = True
    
    # ... rest of existing code ...
```

### Step 5: Update the command-line help

Update the argparse configuration:

```python
parser.add_argument(
    '--view',
    type=ViewMode,
    default=ViewMode.one,
    choices=list(ViewMode),
    help='Display mode (off, one, all, sparkline). Hotkey: "v".'
)
```

## Creating a Load Generator

This recipe shows how to create a load generator script to test cubestat visualization.

### Step 1: Create a new script

Create a new file in the `scripts` directory, for example, `load_generator.py`:

```python
#!/usr/bin/env python3
"""
Load generator for testing cubestat visualizations.

This script generates artificial system load to test cubestat's 
visualization capabilities.
"""

import argparse
import time
import os
import random
import multiprocessing
from typing import List, Callable

def cpu_load(duration: int, intensity: float = 1.0) -> None:
    """Generate CPU load.
    
    Args:
        duration: Duration in seconds
        intensity: Load intensity (0.0-1.0)
    """
    end_time = time.time() + duration
    
    while time.time() < end_time:
        # Adjust work/sleep ratio based on intensity
        work_time = intensity * 0.01  # 10ms at full intensity
        sleep_time = 0.01 - work_time
        
        # Generate CPU load
        start = time.time()
        while time.time() - start < work_time:
            # Busy loop to generate CPU load
            x = 0
            for i in range(1000):
                x += i * i
        
        # Sleep to achieve desired intensity
        if sleep_time > 0:
            time.sleep(sleep_time)

def memory_load(duration: int, size_mb: int) -> None:
    """Allocate memory to test memory metrics.
    
    Args:
        duration: Duration in seconds
        size_mb: Memory to allocate in MB
    """
    # Allocate memory (size_mb megabytes)
    data = bytearray(size_mb * 1024 * 1024)
    
    # Touch the memory to ensure it's actually allocated
    for i in range(0, len(data), 4096):
        data[i] = 1
    
    # Hold the allocation for the specified duration
    time.sleep(duration)
    
    # Return the memory (garbage collection will free it)

def disk_load(duration: int, size_mb: int, path: str = "/tmp") -> None:
    """Generate disk I/O load.
    
    Args:
        duration: Duration in seconds
        size_mb: File size in MB
        path: Directory to write to
    """
    filename = os.path.join(path, f"cubestat_test_{os.getpid()}.tmp")
    chunk_size = 1024 * 1024  # 1MB chunks
    
    try:
        # Write to disk
        with open(filename, "wb") as f:
            for _ in range(size_mb):
                f.write(os.urandom(chunk_size))
                f.flush()
                time.sleep(0.1)  # Control write speed
        
        # Read from disk
        with open(filename, "rb") as f:
            while True:
                data = f.read(chunk_size)
                if not data:
                    break
                time.sleep(0.1)  # Control read speed
    
    finally:
        # Clean up
        if os.path.exists(filename):
            os.remove(filename)

def network_load(duration: int, size_mb: int) -> None:
    """Simulate network load (actual traffic not generated).
    
    Args:
        duration: Duration in seconds
        size_mb: Amount of "network" data to process
    """
    chunk_size = 1024 * 1024  # 1MB chunks
    
    for _ in range(size_mb):
        # Process a chunk of data (simulate network activity)
        data = os.urandom(chunk_size)
        # Do something with the data
        _ = len(data)
        time.sleep(0.5)  # Control "network" speed

def run_load_pattern(pattern: List[Callable], duration: int) -> None:
    """Run a load pattern with multiple load generators.
    
    Args:
        pattern: List of load generator functions to run
        duration: Total duration in seconds
    """
    processes = []
    
    # Start all load generators
    for load_func in pattern:
        p = multiprocessing.Process(target=load_func)
        p.start()
        processes.append(p)
    
    # Wait for the specified duration
    time.sleep(duration)
    
    # Terminate all processes
    for p in processes:
        p.terminate()
        p.join()

def main() -> None:
    """Main function."""
    parser = argparse.ArgumentParser(description="Generate system load for testing cubestat")
    
    parser.add_argument("--duration", type=int, default=60,
                       help="Duration in seconds")
    parser.add_argument("--cpu", type=float, default=0.7,
                       help="CPU load intensity (0.0-1.0)")
    parser.add_argument("--memory", type=int, default=500,
                       help="Memory to allocate in MB")
    parser.add_argument("--disk", type=int, default=100,
                       help="Disk I/O in MB")
    parser.add_argument("--cores", type=int, default=multiprocessing.cpu_count(),
                       help="Number of CPU cores to use")
    
    args = parser.parse_args()
    
    print(f"Generating load for {args.duration} seconds...")
    
    # Create load pattern
    pattern = []
    
    # Add CPU load generators
    for _ in range(args.cores):
        pattern.append(lambda: cpu_load(args.duration, args.cpu))
    
    # Add memory load
    pattern.append(lambda: memory_load(args.duration, args.memory))
    
    # Add disk load
    pattern.append(lambda: disk_load(args.duration, args.disk))
    
    # Add network load simulation
    pattern.append(lambda: network_load(args.duration, args.disk))
    
    # Run the load pattern
    run_load_pattern(pattern, args.duration)
    
    print("Load generation complete.")

if __name__ == "__main__":
    main()
```

### Step 2: Make the script executable

```bash
chmod +x scripts/load_generator.py
```

### Step 3: Run cubestat with the load generator

Open two terminal windows. In the first, start cubestat:

```bash
cubestat
```

In the second, run the load generator:

```bash
python scripts/load_generator.py --duration 30 --cpu 0.8 --memory 1000 --disk 200
```

This will generate a 30-second load pattern that exercises CPU, memory, and disk metrics, allowing you to observe how cubestat visualizes the load.

### Step 4: Experiment with different load patterns

Create different load patterns to test specific aspects of your system:

```bash
# High CPU load
python scripts/load_generator.py --duration 20 --cpu 1.0 --memory 100 --disk 50

# High memory load
python scripts/load_generator.py --duration 20 --cpu 0.3 --memory 2000 --disk 50

# High disk I/O
python scripts/load_generator.py --duration 20 --cpu 0.3 --memory 100 --disk 500
```

This allows you to verify that cubestat correctly visualizes different types of system load.