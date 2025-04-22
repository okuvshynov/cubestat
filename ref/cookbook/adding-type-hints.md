# Adding Type Hints to Legacy Code

This tutorial demonstrates how to add type hints to existing code in cubestat, following the modernization plan.

## Step 1: Set up type checking infrastructure

Ensure you have mypy configured properly:

```bash
pip install mypy
```

And verify the mypy.ini configuration file exists with appropriate settings:

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

## Step 2: Add imports and type variables

At the top of the file, add the necessary imports:

```python
from typing import Any, Dict, List, Optional, Sequence, Tuple, TypeVar, Union
```

If needed, define type variables for generic methods:

```python
T = TypeVar('T', bound='DisplayMode')
```

## Step 3: Add type hints to function signatures

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

## Step 4: Add class variable and attribute type hints

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

## Step 5: Run the type checker

Verify your type hints with mypy:

```bash
mypy cubestat
```

Fix any type errors that are reported.

## Step 6: Handle complex type scenarios

### Using Union types for variables that can have multiple types:

```python
def process_value(value: Union[int, float, str]) -> float:
    if isinstance(value, str):
        return float(value)
    return float(value)
```

### Using Optional for variables that might be None:

```python
def get_metric_value(metrics: Dict[str, float], key: str) -> Optional[float]:
    return metrics.get(key)
```

### Using TypedDict for structured dictionaries:

```python
from typing import TypedDict

class MetricData(TypedDict):
    title: str
    value: float
    unit: str

def format_metric(data: MetricData) -> str:
    return f"{data['title']}: {data['value']}{data['unit']}"
```

## Step 7: Document types with docstrings

Always add docstrings that describe the expected types:

```python
def calculate_rate(current: float, previous: float, interval: float) -> float:
    """Calculate rate of change per second.
    
    Args:
        current: Current measurement value
        previous: Previous measurement value
        interval: Time interval in seconds
        
    Returns:
        Rate of change in units per second
    """
    return (current - previous) / interval
```

## Type Annotation Patterns in Cubestat

### 1. Metrics:

```python
from typing import Dict, List, Tuple, Any

class base_metric:
    def read(self, context: Dict[str, Any]) -> Dict[str, float]:
        """Read metric data.
        
        Args:
            context: System context data
            
        Returns:
            Dictionary mapping metric names to values
        """
        pass
        
    def format(self, title: str, values: List[float], idxs: List[int]) -> Tuple[float, List[str]]:
        """Format metric values.
        
        Args:
            title: Metric title
            values: List of values
            idxs: Indices to format
            
        Returns:
            Tuple of (max_value, formatted_values)
        """
        pass
```

### 2. Platform Modules:

```python
from typing import Callable, Dict, Any

class PlatformBase:
    def loop(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Run data collection loop.
        
        Args:
            callback: Function to call with collected data
        """
        pass
```

### 3. Data Processing:

```python
from typing import List, Dict, Tuple, Optional

def prepare_cells(
    data: List[Dict[str, float]], 
    width: int, 
    key: str
) -> Tuple[List[float], Optional[float]]:
    """Prepare cell data for display.
    
    Args:
        data: Historical data points
        width: Display width
        key: Metric key to prepare
        
    Returns:
        Tuple of (values_list, maximum_value)
    """
    pass
```

## Common Type Hint Challenges

### Challenge 1: External libraries without types

For libraries that don't have type annotations:

```python
# Create type stubs in a file like third_party_stubs.py
import sys
from typing import Any, Dict, List

if sys.version_info >= (3, 8):
    from typing import TypedDict
else:
    from typing_extensions import TypedDict

class NvidiaGPUInfo(TypedDict):
    name: str
    uuid: str
    temperature: int
    utilization: Dict[str, int]
    memory: Dict[str, int]

# Then use these in your code
from third_party_stubs import NvidiaGPUInfo

def get_gpu_info() -> List[NvidiaGPUInfo]:
    # Implementation
    pass
```

### Challenge 2: Dynamic attribute access

When you have dynamic attribute access:

```python
from typing import Any, Dict, cast

def configure_from_args(self, args: Any) -> None:
    """Configure from command line arguments.
    
    Args:
        args: Parsed command line arguments
    """
    # Option 1: Use hasattr/getattr
    if hasattr(args, 'debug'):
        self.debug = bool(getattr(args, 'debug'))
        
    # Option 2: Use cast when you know the structure
    args_dict = cast(Dict[str, Any], vars(args))
    if 'debug' in args_dict:
        self.debug = bool(args_dict['debug'])
```

## Next Steps

- [Creating Unit Tests](./creating-unit-tests.md)
- [Implementing Proper Logging](./implementing-logging.md)
- [Optimizing Data Collection](./optimizing-data-collection.md)