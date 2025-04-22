# Custom Data Exporters

This tutorial shows how to implement custom data exporters for cubestat, allowing metrics to be exported to various formats and systems.

## Step 1: Create a base exporter class

First, create a base class that defines the interface for all exporters:

```python
# cubestat/exporters/base_exporter.py
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

class BaseExporter(ABC):
    """Base class for all data exporters."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the exporter.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.enabled = True
    
    @abstractmethod
    def export(self, metrics: Dict[str, float], timestamp: float) -> None:
        """Export metrics data.
        
        Args:
            metrics: Dictionary mapping metric names to values
            timestamp: UNIX timestamp for the metrics
        """
        pass
    
    def start(self) -> None:
        """Start the exporter (if needed)."""
        pass
    
    def stop(self) -> None:
        """Stop the exporter and perform cleanup."""
        pass
    
    @property
    def name(self) -> str:
        """Get the name of this exporter."""
        return self.__class__.__name__
```

## Step 2: Create a CSV file exporter

Let's implement a CSV file exporter:

```python
# cubestat/exporters/csv_exporter.py
import csv
import os
import time
from typing import Dict, Any, List, Optional, Set, TextIO

from cubestat.exporters.base_exporter import BaseExporter

class CSVExporter(BaseExporter):
    """Export metrics to a CSV file."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the CSV exporter.
        
        Args:
            config: Configuration dictionary with options:
                - filename: Path to CSV file (required)
                - append: Whether to append to existing file (default: False)
        """
        super().__init__(config)
        
        if not self.config.get('filename'):
            raise ValueError("CSV exporter requires 'filename' configuration")
            
        self.filename = self.config['filename']
        self.append = self.config.get('append', False)
        self.file = None
        self.writer = None
        self.known_metrics: Set[str] = set()
        self.header_written = False
    
    def start(self) -> None:
        """Open the CSV file for writing."""
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(self.filename), exist_ok=True)
        
        # Open file for writing or appending
        mode = 'a' if self.append else 'w'
        self.file = open(self.filename, mode, newline='')
        self.writer = csv.writer(self.file)
        
        # If appending and file is empty, we need to write header
        if self.append and os.path.getsize(self.filename) == 0:
            self.header_written = False
        else:
            self.header_written = self.append
    
    def export(self, metrics: Dict[str, float], timestamp: float) -> None:
        """Export metrics to CSV.
        
        Args:
            metrics: Dictionary mapping metric names to values
            timestamp: UNIX timestamp for the metrics
        """
        if not self.writer:
            self.start()
            
        # Update known metrics (columns)
        self.known_metrics.update(metrics.keys())
        
        # Write header if needed
        if not self.header_written:
            header = ['timestamp'] + sorted(self.known_metrics)
            self.writer.writerow(header)
            self.header_written = True
        
        # Write data row
        row = [time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))]
        for metric in sorted(self.known_metrics):
            row.append(metrics.get(metric, ''))
            
        self.writer.writerow(row)
        self.file.flush()  # Ensure data is written to disk
    
    def stop(self) -> None:
        """Close the CSV file."""
        if self.file:
            self.file.close()
            self.file = None
            self.writer = None
```

## Step 3: Create a JSON file exporter

Next, let's implement a JSON file exporter:

```python
# cubestat/exporters/json_exporter.py
import json
import os
import time
from typing import Dict, Any, List, Optional, TextIO

from cubestat.exporters.base_exporter import BaseExporter

class JSONExporter(BaseExporter):
    """Export metrics to a JSON file."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the JSON exporter.
        
        Args:
            config: Configuration dictionary with options:
                - filename: Path to JSON file (required)
                - append: Whether to append to existing file (default: False)
                - pretty: Whether to pretty-print JSON (default: False)
        """
        super().__init__(config)
        
        if not self.config.get('filename'):
            raise ValueError("JSON exporter requires 'filename' configuration")
            
        self.filename = self.config['filename']
        self.append = self.config.get('append', False)
        self.pretty = self.config.get('pretty', False)
        self.file = None
        self.data = []
    
    def start(self) -> None:
        """Prepare for exporting."""
        # If appending, load existing data
        if self.append and os.path.exists(self.filename):
            try:
                with open(self.filename, 'r') as f:
                    self.data = json.load(f)
                    # Ensure the loaded data is a list
                    if not isinstance(self.data, list):
                        self.data = []
            except (json.JSONDecodeError, IOError):
                # Start with empty data if file is invalid
                self.data = []
    
    def export(self, metrics: Dict[str, float], timestamp: float) -> None:
        """Export metrics to JSON.
        
        Args:
            metrics: Dictionary mapping metric names to values
            timestamp: UNIX timestamp for the metrics
        """
        if not self.data:
            self.start()
            
        # Add new data point
        self.data.append({
            'timestamp': timestamp,
            'time': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp)),
            'metrics': metrics
        })
        
        # Write to file
        os.makedirs(os.path.dirname(self.filename), exist_ok=True)
        with open(self.filename, 'w') as f:
            if self.pretty:
                json.dump(self.data, f, indent=2)
            else:
                json.dump(self.data, f)
    
    def stop(self) -> None:
        """Clean up resources."""
        # Reset data
        self.data = []
```

## Step 4: Create an InfluxDB exporter

Now, let's create an exporter for InfluxDB:

```python
# cubestat/exporters/influxdb_exporter.py
import time
from typing import Dict, Any, List, Optional
import urllib.request
import urllib.parse
import urllib.error
import logging

from cubestat.exporters.base_exporter import BaseExporter

logger = logging.getLogger("cubestat.exporters.influxdb")

class InfluxDBExporter(BaseExporter):
    """Export metrics to InfluxDB."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the InfluxDB exporter.
        
        Args:
            config: Configuration dictionary with options:
                - url: InfluxDB URL (required, e.g., http://localhost:8086)
                - database: InfluxDB database name (required)
                - measurement: Measurement name (default: 'cubestat')
                - username: InfluxDB username (optional)
                - password: InfluxDB password (optional)
                - tags: Additional tags to include (optional)
        """
        super().__init__(config)
        
        if not self.config.get('url'):
            raise ValueError("InfluxDB exporter requires 'url' configuration")
        if not self.config.get('database'):
            raise ValueError("InfluxDB exporter requires 'database' configuration")
            
        self.url = self.config['url']
        self.database = self.config['database']
        self.measurement = self.config.get('measurement', 'cubestat')
        self.username = self.config.get('username')
        self.password = self.config.get('password')
        self.tags = self.config.get('tags', {})
        
        # Construct the write URL
        write_url = f"{self.url}/write?db={self.database}"
        if self.username and self.password:
            write_url += f"&u={self.username}&p={self.password}"
        self.write_url = write_url
    
    def export(self, metrics: Dict[str, float], timestamp: float) -> None:
        """Export metrics to InfluxDB.
        
        Args:
            metrics: Dictionary mapping metric names to values
            timestamp: UNIX timestamp for the metrics
        """
        if not metrics:
            return
            
        # Convert timestamp to nanoseconds for InfluxDB
        timestamp_ns = int(timestamp * 1e9)
        
        # Format tags
        tags_str = ""
        for tag_name, tag_value in self.tags.items():
            tags_str += f",{tag_name}={tag_value}"
        
        # Create InfluxDB line protocol data
        lines = []
        for name, value in metrics.items():
            # Escape spaces and commas in the metric name
            safe_name = name.replace(' ', '\\ ').replace(',', '\\,')
            
            lines.append(f"{self.measurement}{tags_str} {safe_name}={value} {timestamp_ns}")
        
        data = '\n'.join(lines).encode('utf-8')
        
        # Send data to InfluxDB
        try:
            req = urllib.request.Request(
                self.write_url,
                data=data,
                headers={'Content-Type': 'application/octet-stream'}
            )
            with urllib.request.urlopen(req) as response:
                if response.status != 204:
                    logger.warning(f"InfluxDB write returned status {response.status}")
        except urllib.error.URLError as e:
            logger.error(f"Failed to write to InfluxDB: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error writing to InfluxDB: {str(e)}")
```

## Step 5: Create a Prometheus exporter

Let's implement a Prometheus exporter that serves metrics via HTTP:

```python
# cubestat/exporters/prometheus_exporter.py
import threading
import time
from typing import Dict, Any, List, Optional
from http.server import HTTPServer, BaseHTTPRequestHandler
import logging
import socket

from cubestat.exporters.base_exporter import BaseExporter

logger = logging.getLogger("cubestat.exporters.prometheus")

class PrometheusHandler(BaseHTTPRequestHandler):
    """HTTP request handler for Prometheus metrics."""
    
    def do_GET(self):
        """Handle GET requests."""
        if self.path == '/metrics':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            
            # Get metrics from parent exporter
            metrics = self.server.exporter.get_prometheus_metrics()
            self.wfile.write(metrics.encode('utf-8'))
        else:
            self.send_response(404)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'Not Found')
    
    def log_message(self, format, *args):
        """Override to use the cubestat logger."""
        logger.debug(format % args)


class PrometheusHTTPServer(HTTPServer):
    """HTTP server with reference to the exporter."""
    
    def __init__(self, server_address, RequestHandlerClass, exporter):
        """Initialize with reference to exporter."""
        super().__init__(server_address, RequestHandlerClass)
        self.exporter = exporter


class PrometheusExporter(BaseExporter):
    """Export metrics in Prometheus format via HTTP."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the Prometheus exporter.
        
        Args:
            config: Configuration dictionary with options:
                - port: Port to listen on (default: 9090)
                - address: Address to bind to (default: 127.0.0.1)
                - prefix: Metric prefix (default: 'cubestat')
        """
        super().__init__(config)
        
        self.port = self.config.get('port', 9090)
        self.address = self.config.get('address', '127.0.0.1')
        self.prefix = self.config.get('prefix', 'cubestat')
        
        # Store the latest metrics
        self.latest_metrics: Dict[str, float] = {}
        self.metrics_lock = threading.Lock()
        
        # HTTP server
        self.server = None
        self.server_thread = None
    
    def start(self) -> None:
        """Start the HTTP server in a background thread."""
        if self.server:
            return
            
        try:
            # Create and start the HTTP server
            self.server = PrometheusHTTPServer(
                (self.address, self.port),
                PrometheusHandler,
                self
            )
            
            self.server_thread = threading.Thread(
                target=self.server.serve_forever,
                daemon=True
            )
            self.server_thread.start()
            
            logger.info(f"Prometheus exporter listening on {self.address}:{self.port}")
        except socket.error as e:
            logger.error(f"Failed to start Prometheus exporter: {str(e)}")
            self.server = None
    
    def export(self, metrics: Dict[str, float], timestamp: float) -> None:
        """Store metrics for Prometheus.
        
        Args:
            metrics: Dictionary mapping metric names to values
            timestamp: UNIX timestamp for the metrics
        """
        # Make sure the server is running
        if not self.server:
            self.start()
        
        # Update the latest metrics
        with self.metrics_lock:
            self.latest_metrics = metrics.copy()
    
    def get_prometheus_metrics(self) -> str:
        """Format metrics in Prometheus exposition format.
        
        Returns:
            Metrics in Prometheus text format
        """
        lines = []
        
        with self.metrics_lock:
            for name, value in self.latest_metrics.items():
                # Convert metric name to Prometheus format
                # Replace spaces and non-alphanumeric chars with underscores
                prom_name = ''.join(
                    c if c.isalnum() else '_' for c in name.lower()
                )
                # Ensure the name starts with a letter
                if not prom_name[0].isalpha():
                    prom_name = 'metric_' + prom_name
                
                # Add prefix
                prom_name = f"{self.prefix}_{prom_name}"
                
                # Add metric to output
                lines.append(f"# HELP {prom_name} Cubestat metric: {name}")
                lines.append(f"# TYPE {prom_name} gauge")
                lines.append(f"{prom_name} {value}")
        
        return '\n'.join(lines) + '\n'
    
    def stop(self) -> None:
        """Stop the HTTP server."""
        if self.server:
            self.server.shutdown()
            self.server = None
            if self.server_thread:
                self.server_thread.join(1.0)  # Wait for thread to terminate
                self.server_thread = None
```

## Step 6: Implement an exporter registry

Create a registry to manage all exporters:

```python
# cubestat/exporters/registry.py
from typing import Dict, List, Any, Type, Optional
import importlib
import logging

from cubestat.exporters.base_exporter import BaseExporter

logger = logging.getLogger("cubestat.exporters")

class ExporterRegistry:
    """Registry for data exporters."""
    
    def __init__(self) -> None:
        """Initialize the registry."""
        self.exporters: Dict[str, BaseExporter] = {}
        self.exporter_classes: Dict[str, Type[BaseExporter]] = {}
    
    def register_exporter_class(self, name: str, exporter_class: Type[BaseExporter]) -> None:
        """Register an exporter class.
        
        Args:
            name: Name for the exporter type
            exporter_class: Exporter class
        """
        self.exporter_classes[name] = exporter_class
    
    def create_exporter(self, name: str, exporter_type: str, config: Optional[Dict[str, Any]] = None) -> None:
        """Create and register an exporter instance.
        
        Args:
            name: Unique name for this exporter instance
            exporter_type: Type of exporter to create
            config: Exporter configuration
        
        Raises:
            ValueError: If exporter_type is not registered
        """
        if exporter_type not in self.exporter_classes:
            raise ValueError(f"Unknown exporter type: {exporter_type}")
        
        # Create the exporter
        exporter_class = self.exporter_classes[exporter_type]
        try:
            exporter = exporter_class(config)
            self.exporters[name] = exporter
            logger.info(f"Created {exporter_type} exporter: {name}")
        except Exception as e:
            logger.error(f"Failed to create {exporter_type} exporter: {str(e)}")
    
    def get_exporter(self, name: str) -> Optional[BaseExporter]:
        """Get an exporter by name.
        
        Args:
            name: Name of the exporter
            
        Returns:
            The exporter instance, or None if not found
        """
        return self.exporters.get(name)
    
    def start_all(self) -> None:
        """Start all exporters."""
        for name, exporter in self.exporters.items():
            try:
                exporter.start()
                logger.info(f"Started exporter: {name}")
            except Exception as e:
                logger.error(f"Failed to start exporter {name}: {str(e)}")
    
    def stop_all(self) -> None:
        """Stop all exporters."""
        for name, exporter in self.exporters.items():
            try:
                exporter.stop()
                logger.info(f"Stopped exporter: {name}")
            except Exception as e:
                logger.error(f"Failed to stop exporter {name}: {str(e)}")
    
    def export_metrics(self, metrics: Dict[str, float], timestamp: float) -> None:
        """Export metrics to all enabled exporters.
        
        Args:
            metrics: Dictionary mapping metric names to values
            timestamp: UNIX timestamp for the metrics
        """
        for name, exporter in self.exporters.items():
            if exporter.enabled:
                try:
                    exporter.export(metrics, timestamp)
                except Exception as e:
                    logger.error(f"Error in exporter {name}: {str(e)}")
```

## Step 7: Add exporter initialization

Initialize exporters in the main application:

```python
# In cubestat/cubestat.py
from cubestat.exporters.registry import ExporterRegistry
from cubestat.exporters.csv_exporter import CSVExporter
from cubestat.exporters.json_exporter import JSONExporter
from cubestat.exporters.influxdb_exporter import InfluxDBExporter
from cubestat.exporters.prometheus_exporter import PrometheusExporter

def init_exporters():
    """Initialize and register exporters."""
    registry = ExporterRegistry()
    
    # Register exporter classes
    registry.register_exporter_class('csv', CSVExporter)
    registry.register_exporter_class('json', JSONExporter)
    registry.register_exporter_class('influxdb', InfluxDBExporter)
    registry.register_exporter_class('prometheus', PrometheusExporter)
    
    return registry

class Cubestat:
    def __init__(self, args):
        # Other initialization...
        
        # Initialize exporters
        self.exporter_registry = init_exporters()
        
        # Create exporters based on command-line arguments
        if args.output:
            if args.output == 'csv':
                self.exporter_registry.create_exporter(
                    'csv_output',
                    'csv',
                    {
                        'filename': args.output_file or 'cubestat.csv',
                        'append': args.append_output
                    }
                )
            elif args.output == 'json':
                self.exporter_registry.create_exporter(
                    'json_output',
                    'json',
                    {
                        'filename': args.output_file or 'cubestat.json',
                        'append': args.append_output,
                        'pretty': True
                    }
                )
            elif args.output == 'influxdb':
                self.exporter_registry.create_exporter(
                    'influxdb_output',
                    'influxdb',
                    {
                        'url': args.influxdb_url or 'http://localhost:8086',
                        'database': args.influxdb_db or 'cubestat',
                        'measurement': 'system_metrics'
                    }
                )
            elif args.output == 'prometheus':
                self.exporter_registry.create_exporter(
                    'prometheus_output',
                    'prometheus',
                    {
                        'port': args.prometheus_port or 9090
                    }
                )
        
        # Start all exporters
        self.exporter_registry.start_all()
```

## Step 8: Update the main loop to export metrics

Modify the main application loop to export metrics:

```python
def run(self):
    """Run the application."""
    # Start the platform
    self.platform.loop(self.data_callback)
    
    # Main event loop
    while self.running:
        # Process user input
        self.input_handler.handle_input()
        
        # Render the screen if needed
        if self.needs_update:
            self.render()
            self.needs_update = False

def data_callback(self, context):
    """Handle incoming data."""
    # Read metrics
    flat_metrics = {}
    
    # Read from all metrics
    for metric in self.metrics:
        values = metric.read(context)
        flat_metrics.update(values)
    
    # Add to data store
    self.data_manager.add_data_point(flat_metrics)
    
    # Export metrics
    self.exporter_registry.export_metrics(
        flat_metrics,
        context.get('timestamp', time.time())
    )
    
    # Mark screen for update
    self.needs_update = True
```

## Step 9: Add cleanup on exit

Make sure to clean up exporters when the application exits:

```python
def stop(self):
    """Stop the application."""
    # Stop the platform
    self.platform.stop()
    
    # Stop all exporters
    self.exporter_registry.stop_all()
    
    # Other cleanup...
```

## Step 10: Add command-line options for exporters

Add command-line options for configuring exporters:

```python
def configure_argparse(parser):
    # Existing arguments...
    
    # Add exporter options
    exporter_group = parser.add_argument_group('Data Export Options')
    exporter_group.add_argument(
        '--output',
        choices=['terminal', 'csv', 'json', 'influxdb', 'prometheus'],
        help='Output format'
    )
    exporter_group.add_argument(
        '--output-file',
        help='File to write output to (for csv/json formats)'
    )
    exporter_group.add_argument(
        '--append-output',
        action='store_true',
        help='Append to output file instead of overwriting'
    )
    
    # InfluxDB options
    influxdb_group = parser.add_argument_group('InfluxDB Options')
    influxdb_group.add_argument(
        '--influxdb-url',
        help='InfluxDB URL (default: http://localhost:8086)'
    )
    influxdb_group.add_argument(
        '--influxdb-db',
        help='InfluxDB database name (default: cubestat)'
    )
    influxdb_group.add_argument(
        '--influxdb-user',
        help='InfluxDB username'
    )
    influxdb_group.add_argument(
        '--influxdb-pass',
        help='InfluxDB password'
    )
    
    # Prometheus options
    prometheus_group = parser.add_argument_group('Prometheus Options')
    prometheus_group.add_argument(
        '--prometheus-port',
        type=int,
        help='Prometheus exporter port (default: 9090)'
    )
    prometheus_group.add_argument(
        '--prometheus-address',
        help='Prometheus exporter bind address (default: 127.0.0.1)'
    )
```

## Best Practices for Data Exporters

1. **Handle errors gracefully**: Exporters should catch and log errors, but not crash the main application.

2. **Efficiently format data**: Optimize data formatting for large metric sets.

3. **Use batching when appropriate**: For network exporters, consider batching data to reduce overhead.

4. **Provide clear error messages**: Log detailed information when export operations fail.

5. **Support configuration options**: Make exporters highly configurable to work in different environments.

6. **Use async operations**: For network exporters, use asynchronous operations to avoid blocking the main application.

7. **Respect resource limits**: Be mindful of resource usage, especially for long-running applications.

8. **Support secure connections**: For exporters that send data over the network, support secure connections (HTTPS, authentication, etc.).

## Next Steps

- [Integration with External Tools](./integration-with-external-tools.md)
- [Optimizing Data Collection](./optimizing-data-collection.md)
- [Adding Command-Line Options](./adding-command-line-options.md)