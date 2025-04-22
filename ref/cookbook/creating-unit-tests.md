# Creating Unit Tests

This tutorial demonstrates how to create unit tests for cubestat components.

## Step 1: Understand the testing framework

Cubestat uses Python's built-in `unittest` framework for testing. Tests are located in the `cubestat/tests/` directory.

## Step 2: Create a test file

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

## Step 3: Run the tests

Run the tests to verify your implementation:

```bash
# Run all tests
python -m unittest discover

# Run just your test
python -m unittest cubestat.tests.test_your_module
```

## Testing Patterns for Cubestat

### Pattern 1: Testing formatting functions

```python
class TestFormatMeasurement(unittest.TestCase):
    """Test formatting of measurements."""
    
    def test_format_bytes(self) -> None:
        """Test formatting of byte values."""
        # Define buckets for byte formatting
        buckets = [(1, "B"), (1024, "KB"), (1024*1024, "MB"), (1024*1024*1024, "GB")]
        
        # Test various values
        self.assertEqual(format_measurement(1023, 2000, buckets), "1023.0B")
        self.assertEqual(format_measurement(1024, 2000, buckets), "1.0KB")
        self.assertEqual(format_measurement(1024*1024, 2000*1024, buckets), "1.0MB")
        self.assertEqual(format_measurement(2*1024*1024*1024, 4*1024*1024*1024, buckets), "2.0GB")
```

### Pattern 2: Testing rate calculations

```python
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

### Pattern 3: Testing metrics

```python
class TestCpuMetric(unittest.TestCase):
    """Test cases for CPU metric."""
    
    def setUp(self) -> None:
        """Set up test environment."""
        self.metric = cpu_metric()
        
    def test_read_with_mock_context(self) -> None:
        """Test reading CPU metrics from mock context."""
        # Create a mock context with CPU data
        mock_context = {
            'cpu': {
                'percent': [10.0, 20.0, 30.0, 40.0]  # 4 CPU cores
            }
        }
        
        # Read metrics
        result = self.metric.read(mock_context)
        
        # Verify results
        self.assertIn('CPU %', result)
        self.assertEqual(result['CPU %'], 25.0)  # Average of all cores
        
        for i, pct in enumerate([10.0, 20.0, 30.0, 40.0]):
            key = f'CPU {i} %'
            self.assertIn(key, result)
            self.assertEqual(result[key], pct)
    
    def test_format(self) -> None:
        """Test formatting of CPU values."""
        title = 'CPU %'
        values = [0.0, 25.0, 50.0, 75.0, 100.0]
        idxs = [0, 1, 2, 3, 4]
        
        max_val, formatted = self.metric.format(title, values, idxs)
        
        # Check maximum value
        self.assertEqual(max_val, 100.0)
        
        # Check formatted values
        self.assertEqual(formatted, ['0.0%', '25.0%', '50.0%', '75.0%', '100.0%'])
```

### Pattern 4: Using mocks for external dependencies

```python
from unittest.mock import patch, MagicMock

class TestGpuMetric(unittest.TestCase):
    """Test cases for GPU metric."""
    
    def setUp(self) -> None:
        """Set up test environment."""
        self.metric = gpu_metric()
    
    @patch('cubestat.metrics.gpu.pynvml')
    def test_nvidia_gpu_read(self, mock_pynvml) -> None:
        """Test reading NVIDIA GPU metrics."""
        # Configure mock
        mock_pynvml.nvmlInit.return_value = None
        mock_pynvml.nvmlDeviceGetCount.return_value = 2
        
        # Create mock devices
        mock_device1 = MagicMock()
        mock_device2 = MagicMock()
        mock_pynvml.nvmlDeviceGetHandleByIndex.side_effect = [mock_device1, mock_device2]
        
        # Configure device responses
        mock_util1 = MagicMock()
        mock_util1.gpu = 50
        mock_util1.memory = 30
        
        mock_util2 = MagicMock()
        mock_util2.gpu = 70
        mock_util2.memory = 60
        
        mock_pynvml.nvmlDeviceGetUtilizationRates.side_effect = [mock_util1, mock_util2]
        
        mock_memory1 = MagicMock()
        mock_memory1.used = 2 * 1024 * 1024 * 1024  # 2 GB
        mock_memory1.total = 8 * 1024 * 1024 * 1024  # 8 GB
        
        mock_memory2 = MagicMock()
        mock_memory2.used = 4 * 1024 * 1024 * 1024  # 4 GB
        mock_memory2.total = 8 * 1024 * 1024 * 1024  # 8 GB
        
        mock_pynvml.nvmlDeviceGetMemoryInfo.side_effect = [mock_memory1, mock_memory2]
        
        # Call the method under test
        result = self.metric.read({})
        
        # Verify the results
        self.assertEqual(result['GPU 0 %'], 50.0)
        self.assertEqual(result['GPU 1 %'], 70.0)
        self.assertEqual(result['GPU 0 mem %'], 25.0)  # 2GB/8GB = 25%
        self.assertEqual(result['GPU 1 mem %'], 50.0)  # 4GB/8GB = 50%
```

## Best Practices for Testing in Cubestat

### 1. Write test-friendly code

Design your code with testing in mind:

- Separate data collection from processing logic
- Use dependency injection where possible
- Create pure functions that are easy to test
- Avoid global state

### 2. Test edge cases

Ensure your tests cover edge cases:

- Zero values
- Negative values (if applicable)
- Maximum values
- Empty inputs
- Missing keys in dictionaries
- Null/None values

### 3. Test error handling

Verify that your code handles errors gracefully:

```python
def test_missing_data_handling(self) -> None:
    """Test handling of missing data."""
    # Create a context with missing CPU data
    context = {}
    
    # Read should not throw an exception
    result = self.metric.read(context)
    
    # Should return an empty dictionary
    self.assertEqual(result, {})
```

### 4. Use setUp and tearDown

Use `setUp` and `tearDown` methods to handle common test setup and cleanup:

```python
def setUp(self) -> None:
    """Setup test environment."""
    # Create a temporary file for testing
    self.temp_file = tempfile.NamedTemporaryFile(delete=False)
    self.temp_file.write(b"test data")
    self.temp_file.close()
    
def tearDown(self) -> None:
    """Clean up after test."""
    # Remove the temporary file
    if os.path.exists(self.temp_file.name):
        os.unlink(self.temp_file.name)
```

### 5. Use parameterized tests

For testing multiple similar cases:

```python
class TestFormatting(unittest.TestCase):
    """Test formatting functions."""
    
    def test_format_percentage(self) -> None:
        """Test percentage formatting with various values."""
        test_cases = [
            (0.0, "0.0%"),
            (50.0, "50.0%"),
            (100.0, "100.0%"),
            (0.123, "0.1%"),  # Should round to 1 decimal place
        ]
        
        for value, expected in test_cases:
            with self.subTest(value=value):
                result = format_percentage(value)
                self.assertEqual(result, expected)
```

## Next Steps

- [Implementing Proper Logging](./implementing-logging.md)
- [Building Custom Visualizations](./building-custom-visualizations.md)
- [Creating Load Generators](./creating-load-generators.md)