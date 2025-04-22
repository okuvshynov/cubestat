# Cross-Platform Testing

This tutorial demonstrates how to effectively test cubestat across multiple platforms to ensure cross-platform compatibility.

## Step 1: Understand platform-specific code

Cubestat uses platform-specific code to collect metrics on different operating systems. This is organized through:

1. A platform factory in `platforms/factory.py` that selects the appropriate implementation
2. Platform-specific implementations in `platforms/linux.py` and `platforms/macos.py`
3. Platform-specific metric implementations through the `@cubestat_metric` decorator

## Step 2: Set up a testing framework

Create a testing framework that supports platform-specific tests:

```python
# cubestat/tests/platform_helpers.py
import platform
import unittest
import sys
from typing import List, Optional, Type

def skip_if_not_platform(required_platform: str):
    """Decorator to skip tests on unsupported platforms.
    
    Args:
        required_platform: Platform name (darwin, linux, win32) required for the test
    """
    current_platform = sys.platform
    
    def decorator(test_item):
        if current_platform != required_platform:
            return unittest.skip(f"Test requires {required_platform}, but running on {current_platform}")(test_item)
        return test_item
    
    return decorator

def run_platform_tests(test_classes: List[Type[unittest.TestCase]], 
                       platform_name: Optional[str] = None) -> unittest.TestResult:
    """Run tests for a specific platform or the current platform.
    
    Args:
        test_classes: List of TestCase classes to run
        platform_name: Platform to run tests for, or None for current platform
        
    Returns:
        Test result object
    """
    current_platform = platform_name or sys.platform
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    for test_class in test_classes:
        # Check if the test is platform-specific
        if hasattr(test_class, 'platform') and test_class.platform != current_platform:
            continue
            
        suite.addTest(loader.loadTestsFromTestCase(test_class))
    
    runner = unittest.TextTestRunner()
    return runner.run(suite)
```

## Step 3: Create platform-specific test cases

Create test cases for each platform:

```python
# cubestat/tests/test_linux_platform.py
import unittest
import sys
from unittest.mock import patch, MagicMock
from cubestat.tests.platform_helpers import skip_if_not_platform

@skip_if_not_platform('linux')
class TestLinuxPlatform(unittest.TestCase):
    """Test Linux platform-specific functionality."""
    
    platform = 'linux'
    
    def setUp(self) -> None:
        """Set up the test environment."""
        from cubestat.platforms.linux import LinuxPlatform
        self.platform = LinuxPlatform(1000)  # 1 second interval
    
    def tearDown(self) -> None:
        """Clean up after tests."""
        if hasattr(self, 'platform'):
            self.platform.stop()
    
    def test_init(self) -> None:
        """Test platform initialization."""
        self.assertEqual(self.platform.interval_s, 1.0)
        self.assertFalse(self.platform.running)
        self.assertIsNone(self.platform.thread)
    
    @patch('builtins.open')
    def test_read_proc_stat(self, mock_open) -> None:
        """Test reading /proc/stat."""
        # Mock the file content
        mock_file = MagicMock()
        mock_file.__enter__.return_value.readlines.return_value = [
            "cpu  1000 200 300 4000 500 600 700 800 900 1000\n",
            "cpu0 100 20 30 400 50 60 70 80 90 100\n",
            "cpu1 100 20 30 400 50 60 70 80 90 100\n"
        ]
        mock_open.return_value = mock_file
        
        # Call the method
        result = self.platform._read_proc_stat()
        
        # Verify results
        self.assertIn('cpu', result)
        self.assertEqual(len(result['cpu']), 10)
        self.assertEqual(result['cpu'][0], 1000)
        self.assertEqual(result['cpu'][3], 4000)
        
        self.assertEqual(len(result), 3)  # total + 2 CPUs
        self.assertIn('cpu0', result)
        self.assertIn('cpu1', result)
```

```python
# cubestat/tests/test_macos_platform.py
import unittest
import sys
import subprocess
from unittest.mock import patch, MagicMock
from cubestat.tests.platform_helpers import skip_if_not_platform

@skip_if_not_platform('darwin')
class TestMacOSPlatform(unittest.TestCase):
    """Test macOS platform-specific functionality."""
    
    platform = 'darwin'
    
    def setUp(self) -> None:
        """Set up the test environment."""
        from cubestat.platforms.macos import MacOSPlatform
        self.platform = MacOSPlatform(1000)  # 1 second interval
    
    def tearDown(self) -> None:
        """Clean up after tests."""
        if hasattr(self, 'platform'):
            self.platform.stop()
    
    def test_init(self) -> None:
        """Test platform initialization."""
        self.assertEqual(self.platform.interval_s, 1.0)
        self.assertFalse(self.platform.running)
        self.assertIsNone(self.platform.thread)
    
    @patch('subprocess.run')
    def test_read_sysctl(self, mock_run) -> None:
        """Test reading system information with sysctl."""
        # Mock subprocess output
        mock_result = MagicMock()
        mock_result.stdout = b"hw.ncpu: 4\n"
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        # Call the method
        result = self.platform._read_sysctl("hw.ncpu")
        
        # Verify results
        self.assertEqual(result, "4")
        mock_run.assert_called_once()
        args, kwargs = mock_run.call_args
        self.assertEqual(kwargs['capture_output'], True)
        self.assertEqual(kwargs['text'], False)
        self.assertEqual(args[0][0], "sysctl")
        self.assertEqual(args[0][1], "hw.ncpu")
```

## Step 4: Set up a virtual environment for each platform

For thorough testing, set up a testing environment for each platform:

### Linux using Docker

Create a Dockerfile for testing:

```dockerfile
# Dockerfile.test-linux
FROM python:3.8-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    procps \
    lm-sensors \
    && rm -rf /var/lib/apt/lists/*

# Copy the application
COPY . /app/

# Install dependencies
RUN pip install -e .[dev]

# Run tests
CMD ["python", "-m", "unittest", "discover"]
```

Run the Linux tests:

```bash
docker build -f Dockerfile.test-linux -t cubestat-test-linux .
docker run --rm cubestat-test-linux
```

### macOS using GitHub Actions

Add a GitHub Actions workflow for macOS testing:

```yaml
# .github/workflows/test-macos.yml
name: Test on macOS

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test-macos:
    runs-on: macos-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.8'
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e .[dev]
    - name: Run tests
      run: |
        python -m unittest discover
```

## Step 5: Create mock platforms for testing

For platform-agnostic testing, create mock platforms:

```python
# cubestat/platforms/mock.py
import time
import threading
import random
from typing import Callable, Dict, Any

class MockPlatform:
    """Mock platform for testing."""
    
    def __init__(self, interval_ms: int) -> None:
        """Initialize the mock platform.
        
        Args:
            interval_ms: Refresh interval in milliseconds
        """
        self.interval_s = interval_ms / 1000.0
        self.running = False
        self.thread = None
        
        # Simulated system data
        self.cpu_cores = 4
        self.memory_total = 16 * 1024 * 1024 * 1024  # 16 GB
        self.disk_total = 512 * 1024 * 1024 * 1024  # 512 GB
    
    def loop(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Run the data collection loop.
        
        Args:
            callback: Function to call with collected data
        """
        self.running = True
        
        def _loop():
            last_time = time.time()
            cpu_values = [0.0] * self.cpu_cores
            while self.running:
                try:
                    # Generate simulated data
                    now = time.time()
                    
                    # Simulate CPU usage (random walk)
                    for i in range(self.cpu_cores):
                        # Random walk between 0 and 100
                        cpu_values[i] = max(0.0, min(100.0, cpu_values[i] + random.uniform(-10, 10)))
                    
                    # Simulate memory usage (sinusoidal pattern)
                    memory_used = int(
                        self.memory_total * (0.3 + 0.2 * abs(math.sin(now / 10.0)))
                    )
                    
                    # Simulate disk usage (slowly increasing)
                    disk_used = int(
                        self.disk_total * (0.5 + 0.001 * ((now / 3600) % 100))
                    )
                    
                    # Create context with simulated data
                    context = {
                        'timestamp': now,
                        'mock': {
                            'cpu': {
                                'percent': cpu_values,
                                'average': sum(cpu_values) / len(cpu_values)
                            },
                            'memory': {
                                'total': self.memory_total,
                                'used': memory_used,
                                'free': self.memory_total - memory_used
                            },
                            'disk': {
                                'total': self.disk_total,
                                'used': disk_used,
                                'free': self.disk_total - disk_used
                            }
                        }
                    }
                    
                    # Call the callback with the collected data
                    callback(context)
                    
                    # Sleep to maintain the interval
                    elapsed = time.time() - last_time
                    sleep_time = max(0, self.interval_s - elapsed)
                    time.sleep(sleep_time)
                    last_time = now
                
                except Exception as e:
                    print(f"Error in mock platform loop: {e}")
                    time.sleep(self.interval_s)
        
        self.thread = threading.Thread(target=_loop)
        self.thread.daemon = True
        self.thread.start()
    
    def stop(self) -> None:
        """Stop the data collection loop."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2.0)
```

## Step 6: Add mock metrics

Create mock metrics for testing:

```python
# cubestat/metrics/mock.py
import random
import math
import time
from enum import Enum
from typing import Dict, List, Tuple, Any

from cubestat.metrics.base_metric import base_metric
from cubestat.metrics_registry import cubestat_metric

class MockMode(Enum):
    show = "show"
    hide = "hide"
    
    def __str__(self):
        return self.value

@cubestat_metric('mock')
class mock_cpu_metric(base_metric):
    """Mock CPU metric for testing."""
    
    def __init__(self) -> None:
        """Initialize the mock CPU metric."""
        self.mode = MockMode.show
    
    def read(self, context: Dict[str, Any]) -> Dict[str, float]:
        """Read mock CPU metrics.
        
        Args:
            context: Context dictionary with mock data
            
        Returns:
            Dictionary of CPU metrics
        """
        result = {}
        
        # Extract data from mock context
        if 'mock' in context and 'cpu' in context['mock']:
            cpu_data = context['mock']['cpu']
            
            # Add CPU average
            if 'average' in cpu_data:
                result['CPU %'] = cpu_data['average']
            
            # Add per-core metrics
            if 'percent' in cpu_data:
                for i, value in enumerate(cpu_data['percent']):
                    result[f'CPU {i} %'] = value
        
        return result
    
    def format(self, title: str, values: List[float], idxs: List[int]) -> Tuple[float, List[str]]:
        """Format CPU values.
        
        Args:
            title: Metric title
            values: List of values
            idxs: Indices to format
            
        Returns:
            Tuple of (max_value, formatted_values)
        """
        return 100.0, [f'{values[i]:.1f}%' for i in idxs]
    
    def pre(self, title: str) -> Tuple[bool, int]:
        """Determine if this metric should be displayed.
        
        Args:
            title: Metric title
            
        Returns:
            Tuple of (show_metric, indentation_level)
        """
        return self.mode == MockMode.show, 0
    
    def configure(self, conf):
        """Configure the metric."""
        if hasattr(conf, 'mock_cpu'):
            self.mode = conf.mock_cpu
        return self
    
    @classmethod
    def key(cls) -> str:
        """Return the key that identifies this metric."""
        return 'mock_cpu'
    
    def hotkey(self) -> str:
        """Return the hotkey used to toggle this metric's display mode."""
        return 'm'
    
    @classmethod
    def configure_argparse(cls, parser):
        """Configure command line arguments for this metric."""
        parser.add_argument(
            '--mock-cpu',
            type=MockMode,
            default=MockMode.show,
            choices=list(MockMode),
            help='Show mock CPU metrics. For testing only.'
        )
```

## Step 7: Create platform test scripts

Create scripts to test on each platform:

```bash
#!/bin/bash
# test_all_platforms.sh

echo "Running tests on current platform..."
python -m unittest discover

echo "Building Linux test container..."
docker build -f Dockerfile.test-linux -t cubestat-test-linux .

echo "Running tests on Linux..."
docker run --rm cubestat-test-linux

echo "Tests complete!"
```

## Step 8: Use GitHub Actions for multi-platform CI

Set up GitHub Actions for multi-platform testing:

```yaml
# .github/workflows/multi-platform-test.yml
name: Multi-Platform Tests

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test-linux:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.8'
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e .[dev]
    - name: Run tests
      run: |
        python -m unittest discover

  test-macos:
    runs-on: macos-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.8'
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e .[dev]
    - name: Run tests
      run: |
        python -m unittest discover
```

## Step 9: Handle platform-specific dependencies

Update `setup.py` to handle platform-specific dependencies:

```python
import sys
from setuptools import setup, find_packages

# Common dependencies
install_requires = [
    'psutil>=5.9.0',
]

# Platform-specific dependencies
if sys.platform == 'darwin':
    install_requires.append('pyobjc-framework-SystemConfiguration>=8.5')
elif sys.platform == 'linux':
    install_requires.append('python-xlib>=0.31')

# Optional CUDA support
cuda_requires = [
    'pynvml>=11.0.0',
]

setup(
    name='cubestat',
    version='0.3.4',
    packages=find_packages(),
    install_requires=install_requires,
    extras_require={
        'cuda': cuda_requires,
        'dev': [
            'mypy>=0.910',
            'ruff>=0.0.256',
        ],
    },
    # Other setup parameters...
)
```

## Step 10: Create a compatibility matrix

Document platform compatibility in `README.md`:

```markdown
## Platform Compatibility

Cubestat has been tested on the following platforms:

| Feature       | Linux        | macOS        | Windows      |
|---------------|--------------|--------------|--------------|
| CPU metrics   | ✅ Full      | ✅ Full      | ❌ Planned   |
| Memory metrics| ✅ Full      | ✅ Full      | ❌ Planned   |
| Disk metrics  | ✅ Full      | ✅ Full      | ❌ Planned   |
| Network metrics| ✅ Full     | ✅ Full      | ❌ Planned   |
| GPU metrics   | ✅ NVIDIA    | ✅ Apple     | ❌ Planned   |
| Power metrics | ⚠️ Limited   | ✅ Full      | ❌ Planned   |
| Temperature   | ✅ Full      | ⚠️ Limited   | ❌ Planned   |

Legend:
- ✅ Full: Fully supported
- ⚠️ Limited: Partial support or limitations
- ❌ Planned: Not currently supported, but planned

### Requirements

#### Linux
- Python 3.6+
- `psutil` for system metrics
- `pynvml` for NVIDIA GPU support
- `lm-sensors` for temperature monitoring

#### macOS
- Python 3.6+
- `psutil` for system metrics
- `pyobjc-framework-SystemConfiguration` for network metrics
```

## Best Practices for Cross-Platform Development

1. **Use abstraction layers**: Separate platform-specific code from core logic.

2. **Test on all target platforms**: Regularly run tests on all supported platforms.

3. **Mock platform-specific APIs**: Create mock implementations for testing.

4. **Document platform differences**: Clearly document platform-specific features and limitations.

5. **Handle missing dependencies gracefully**: Gracefully handle the absence of optional dependencies.

6. **Use feature detection**: Detect platform capabilities at runtime rather than hardcoding platform checks.

7. **Use portable path handling**: Use `os.path` for cross-platform path handling.

8. **Handle terminal differences**: Be aware of terminal capabilities and color support differences.

9. **Consider file permissions**: Handle file permission differences between platforms.

10. **Test with CI/CD**: Use CI/CD pipelines to automatically test on multiple platforms.

## Next Steps

- [Implementing Platform-Specific Code](./implementing-platform-specific-code.md)
- [Creating Unit Tests](./creating-unit-tests.md)
- [Optimizing Data Collection](./optimizing-data-collection.md)