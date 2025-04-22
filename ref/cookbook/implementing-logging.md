# Implementing Proper Logging

This tutorial shows how to implement proper logging in cubestat components.

## Step 1: Set up a logger

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

## Step 2: Initialize logging in the application

In the application's initialization (e.g., `__init__.py`):

```python
"""Cubestat - Horizon chart in terminal for system monitoring."""

__version__ = "0.3.4"

from cubestat.logging import configure_logging

# Initialize default logging configuration
configure_logging()
```

## Step 3: Use logging in your code

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

## Step 4: Configure log levels appropriately

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

## Step 5: Add command-line options for logging

Update the argument parser to allow configuring logging:

```python
def configure_argparse(parser):
    # Existing arguments...
    
    # Add logging-related arguments
    parser.add_argument(
        '--log-level',
        choices=['debug', 'info', 'warning', 'error', 'critical'],
        default='info',
        help='Set the logging level'
    )
    parser.add_argument(
        '--log-file',
        help='Log to the specified file'
    )
    parser.add_argument(
        '--no-console-log',
        action='store_true',
        help='Disable logging to console'
    )
```

## Step 6: Initialize logging based on command-line options

In the main application:

```python
def main():
    parser = argparse.ArgumentParser(description="Cubestat - System monitoring with horizon charts")
    configure_argparse(parser)
    args = parser.parse_args()
    
    # Configure logging based on arguments
    log_level = getattr(logging, args.log_level.upper())
    configure_logging(
        level=log_level,
        log_file=args.log_file,
        console=not args.no_console_log
    )
    
    # Rest of application...
```

## Logging Patterns in Cubestat

### 1. Module-specific loggers

Create module-specific loggers to easily identify the source:

```python
# In cubestat/metrics/cpu.py
import logging

logger = logging.getLogger("cubestat.metrics.cpu")

class cpu_metric(base_metric):
    def read(self, context):
        logger.debug("Reading CPU metrics")
        # Implementation...
```

### 2. Context-aware logging

Include relevant context in log messages:

```python
def process_data(data_dict):
    if not data_dict:
        logger.warning("Empty data dictionary received")
        return {}
        
    try:
        result = {}
        for key, value in data_dict.items():
            logger.debug(f"Processing {key} with value {value}")
            # Processing...
            result[key] = processed_value
        return result
    except Exception as e:
        logger.error(f"Error processing data: {e}, data: {data_dict}")
        return {}
```

### 3. Performance logging

Track performance of operations:

```python
import time

def collect_metrics():
    start_time = time.time()
    logger.debug("Starting metrics collection")
    
    # Collection logic...
    
    elapsed = time.time() - start_time
    logger.debug(f"Metrics collection completed in {elapsed:.3f} seconds")
    return metrics
```

### 4. Log rotation

For long-running applications, set up log rotation:

```python
import logging
from logging.handlers import RotatingFileHandler

def configure_logging_with_rotation(
    level=logging.INFO,
    log_file=None,
    max_size=10*1024*1024,  # 10 MB
    backup_count=5
):
    logger = logging.getLogger("cubestat")
    logger.setLevel(level)
    logger.handlers = []
    
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    if log_file:
        handler = RotatingFileHandler(
            log_file,
            maxBytes=max_size,
            backupCount=backup_count
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
```

## Best Practices for Logging

### 1. Be consistent with log levels

- `DEBUG`: Use for detailed troubleshooting
- `INFO`: Use for regular operation events
- `WARNING`: Use for unusual but recoverable situations
- `ERROR`: Use for failures that prevent a function from working
- `CRITICAL`: Use for application-wide failures

### 2. Log structured information

Use structured logging for easier parsing:

```python
def log_metric_state(metric_name, values, formatted):
    logger.debug(
        f"Metric state - "
        f"name: {metric_name}, "
        f"raw_values: {values}, "
        f"formatted: {formatted}"
    )
```

### 3. Avoid excessive logging

Don't log in tight loops or performance-sensitive code paths:

```python
# Bad - logs every iteration
for i in range(1000000):
    logger.debug(f"Processing item {i}")
    # Process...

# Better - log batches
for batch_idx, batch in enumerate(chunks(items, 1000)):
    logger.debug(f"Processing batch {batch_idx}")
    for item in batch:
        # Process without logging
```

### 4. Handle sensitive information

Don't log passwords, API keys, or other sensitive data:

```python
def authenticate(username, password):
    logger.info(f"Authentication attempt for user: {username}")
    # Do NOT log the password
    
    success = auth_service.verify(username, password)
    
    if success:
        logger.info(f"Authentication successful for user: {username}")
    else:
        logger.warning(f"Authentication failed for user: {username}")
    
    return success
```

### 5. Log command-line arguments

Log startup configuration:

```python
def main():
    parser = argparse.ArgumentParser()
    # Configure parser...
    args = parser.parse_args()
    
    # Configure logging
    configure_logging(level=getattr(logging, args.log_level.upper()))
    
    # Log configuration (excluding sensitive args)
    safe_args = vars(args).copy()
    for sensitive_arg in ('password', 'api_key'):
        if sensitive_arg in safe_args:
            safe_args[sensitive_arg] = '****'
    
    logger.info(f"Starting cubestat with configuration: {safe_args}")
    
    # Rest of application...
```

## Next Steps

- [Creating Unit Tests](./creating-unit-tests.md)
- [Optimizing Data Collection](./optimizing-data-collection.md)
- [Adding Command-Line Options](./adding-command-line-options.md)