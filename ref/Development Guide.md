# Development Guide

This guide provides information for developers who want to contribute to the Cubestat project or extend its functionality.

## Development Environment Setup

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- Git (for version control)

### Installation for Development

1. Clone the repository:
   ```bash
   git clone https://github.com/okuvshynov/cubestat.git
   cd cubestat
   ```

2. Install in development mode:
   ```bash
   # Basic installation
   pip install -e .
   
   # With NVIDIA GPU support
   pip install -e .[cuda]
   ```

3. Install development dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```

4. Set up pre-commit hooks (if available):
   ```bash
   pre-commit install
   ```

## Project Structure

- `cubestat/`: Main package directory
  - `__init__.py`: Package initialization
  - `cubestat.py`: Main application class
  - `data.py`: Data management
  - `colors.py`: Color handling
  - `common.py`: Common utilities
  - `input.py`: Input handling
  - `screen.py`: Screen rendering
  - `logging.py`: Logging configuration
  - `metrics_registry.py`: Metrics registration system
  - `metrics/`: Metric implementations
    - `base_metric.py`: Base class for metrics
    - Various metric implementations
  - `platforms/`: Platform-specific code
    - `factory.py`: Platform detection
    - `macos.py`: macOS implementation
    - `linux.py`: Linux implementation
  - `tests/`: Unit tests

## Development Workflow

### Running Tests

```bash
# Run all tests
python -m unittest discover

# Run a specific test
python -m unittest cubestat.tests.test_data_manager
```

### Type Checking

```bash
# Check types with mypy
mypy cubestat
```

### Linting

```bash
# Run linter
ruff check cubestat
```

### Formatting

```bash
# Format code
ruff format cubestat
```

## Adding New Features

### Adding a New Metric

1. Create a new Python file in the `metrics` directory
2. Inherit from `BaseMetric` in `base_metric.py`
3. Implement required methods:
   - `read(context)`: Collect metric data
   - `format(title, values, indices)`: Format for display
   - `pre(title)`: Determine display status
4. Register with the `cubestat_metric` decorator
5. Add command-line configuration as needed
6. Add tests for the new metric

Example:
```python
from cubestat.metrics.base_metric import BaseMetric
from cubestat.metrics_registry import cubestat_metric
from cubestat.common import DisplayMode

class MyDisplayMode(DisplayMode):
    on = "on"
    off = "off"

@cubestat_metric('my_metric')
class MyMetric(BaseMetric):
    def __init__(self, args):
        super().__init__(args)
        self.my_mode = args.my_mode
        
    def read(self, context):
        # Implement metric data collection
        return {'my_value': 42}
        
    def format(self, title, values, indices):
        # Format values for display
        max_value = max(values) if values else 0
        return max_value, [f"{values[i]:.2f}" for i in indices]
        
    def pre(self, title):
        # Determine if and how to display
        return self.my_mode == MyDisplayMode.on, 0
        
    @staticmethod
    def configure_argparse(parser):
        # Add command-line arguments
        parser.add_argument(
            '--my-mode', type=MyDisplayMode, default=MyDisplayMode.on,
            choices=list(MyDisplayMode),
            help='Enable/disable my metric. Can be toggled by pressing m.'
        )
```

### Adding Platform Support

1. Create a new platform implementation in the `platforms` directory
2. Implement the required interface:
   - `__init__(self, interval_ms)`: Initialize with refresh interval
   - `loop(self, do_read_cb)`: Implement data collection loop
3. Update the platform factory to detect and create your platform
4. Ensure metrics handle your platform's context format
5. Add platform-specific tests

### Improving Existing Code

When enhancing existing code:

1. Follow the established code style and patterns
2. Add type hints to all new code and when refactoring existing code
3. Update tests to cover new functionality
4. Document changes with clear comments and docstrings
5. Ensure cross-platform compatibility
6. Handle errors gracefully with appropriate logging

## Coding Standards

### Naming Conventions

- **Files/Functions/Variables**: Use snake_case (e.g., `data_manager.py`, `get_metrics`)
- **Classes**: Use CamelCase for primary classes (e.g., `DataManager`)
- **Constants**: Use UPPER_SNAKE_CASE for constants

### Code Organization

- **Imports**: Standard library first, then project imports
- **Class Structure**: Public methods first, followed by private methods
- **Function Order**: Place related functions together
- **Line Length**: Aim for 88 characters per line (ruff default)

### Documentation

- Add docstrings in Google style format to all functions and classes
- Include type hints for all parameters and return values
- Document exceptions that may be raised
- Provide examples for complex functionality

Example:
```python
def format_measurement(value: float, unit: str = "") -> str:
    """
    Format a measurement value with appropriate units.
    
    Args:
        value: The numeric value to format
        unit: The base unit (e.g., "B" for bytes)
        
    Returns:
        A formatted string with value and unit
        
    Examples:
        >>> format_measurement(1500, "B")
        "1.5 KB"
    """
    # Implementation
```

### Error Handling

- Use specific exceptions rather than catching all exceptions
- Log exceptions with context information
- Provide graceful fallbacks for failures
- Use try/except blocks to isolate potential failure points

Example:
```python
try:
    result = potentially_failing_function()
except SpecificError as e:
    logging.error(f"Failed to process data: {e}")
    result = fallback_value
```

## Release Process

1. Update version in `__init__.py`
2. Update CHANGES.md with new features and fixes
3. Run tests, type checking, and linting
4. Create a new Git tag for the version
5. Build and publish the package

## Getting Help

If you need assistance with development:

1. Check the existing documentation in the `/ref` directory
2. Review the code for similar implementations
3. Run tests to understand expected behavior
4. Reach out to the project maintainers with specific questions