# Adding Command-Line Options

This tutorial demonstrates how to add new command-line options to cubestat, connecting them to application behavior.

## Step 1: Understand the command-line argument system

Cubestat uses Python's `argparse` module for command-line arguments. The main argument parser is configured in `cubestat.py`, but individual metrics can also add their own arguments.

## Step 2: Add a new global option

To add a new global option to cubestat, modify the argument parser in `cubestat.py`:

```python
def configure_argparse(parser):
    """Configure command line arguments."""
    # Existing arguments...
    
    # Add a new argument for refresh rate
    parser.add_argument(
        '--refresh-rate',
        type=int,
        default=1000,
        help='Refresh rate in milliseconds. Default: 1000ms (1 second)'
    )
    
    # Add a new option for display style
    parser.add_argument(
        '--style',
        type=str,
        choices=['default', 'monochrome', 'colorful', 'minimal'],
        default='default',
        help='Visual style to use. Default: default'
    )
```

## Step 3: Connect the option to application behavior

Modify the `Cubestat` class to use the new options:

```python
def __init__(self, args):
    """Initialize cubestat application."""
    # Other initialization...
    
    # Use the refresh rate from command line
    self.refresh_rate = args.refresh_rate
    
    # Use the style setting
    self.style = args.style
    
    # Configure the platform with the refresh rate
    self.platform = get_platform(self.refresh_rate)
    
    # Configure the screen with the style
    if self.style == 'monochrome':
        self.screen = Screen(use_colors=False)
    elif self.style == 'minimal':
        self.screen = Screen(use_colors=True, minimal=True)
    elif self.style == 'colorful':
        self.screen = Screen(use_colors=True, enhanced_colors=True)
    else:  # default
        self.screen = Screen(use_colors=True)
```

## Step 4: Add metric-specific options

Metrics can add their own command-line options through the `configure_argparse` class method. Here's an example for a new network metric option:

```python
# In metrics/network.py
from enum import Enum

class NetworkMode(Enum):
    """Network display modes."""
    show = "show"
    hide = "hide"
    bandwidth = "bandwidth"  # New option to show only bandwidth
    packets = "packets"      # New option to show only packet counts
    
    def __str__(self):
        return self.value

class network_metric(base_metric):
    # Other metric code...
    
    @classmethod
    def configure_argparse(cls, parser):
        """Configure command line arguments for this metric."""
        parser.add_argument(
            '--net',
            type=NetworkMode,
            default=NetworkMode.show,
            choices=list(NetworkMode),
            help='Network metrics display mode. Can be toggled by pressing n.'
        )
```

## Step 5: Handle the metric-specific option

In the metric class, handle the new option:

```python
def configure(self, conf):
    """Configure the network metric."""
    if hasattr(conf, 'net'):
        self.mode = conf.net
        # Special handling for new modes
        if self.mode == NetworkMode.bandwidth:
            self.show_packets = False
            self.show_bandwidth = True
        elif self.mode == NetworkMode.packets:
            self.show_packets = True
            self.show_bandwidth = False
    return self

def read(self, context):
    """Read network metrics."""
    result = {}
    
    # Base implementation...
    
    # Filter results based on mode
    if hasattr(self, 'show_bandwidth') and not self.show_bandwidth:
        # Remove bandwidth metrics
        for key in list(result.keys()):
            if 'bytes' in key.lower() or 'bps' in key.lower():
                del result[key]
                
    if hasattr(self, 'show_packets') and not self.show_packets:
        # Remove packet metrics
        for key in list(result.keys()):
            if 'packet' in key.lower() or 'pkt' in key.lower():
                del result[key]
    
    return result
```

## Step 6: Add a configuration file option

For more complex applications, add support for configuration files:

```python
import configparser
import os

def configure_argparse(parser):
    """Configure command line arguments."""
    # Add config file option
    parser.add_argument(
        '--config',
        type=str,
        help='Path to configuration file'
    )
    
    # Other arguments...

def load_config(args):
    """Load configuration from file, if specified."""
    config = configparser.ConfigParser()
    
    # Default config locations
    default_configs = [
        '/etc/cubestat.conf',
        os.path.expanduser('~/.config/cubestat.conf'),
        os.path.expanduser('~/.cubestat.conf')
    ]
    
    # Try default locations first
    found_config = False
    for config_path in default_configs:
        if os.path.isfile(config_path):
            config.read(config_path)
            found_config = True
            
    # Then try specified config file
    if args.config:
        if os.path.isfile(args.config):
            config.read(args.config)
            found_config = True
        else:
            print(f"Warning: Config file {args.config} not found")
    
    if found_config:
        # Override arguments with config file settings
        for section in config.sections():
            for key, value in config.items(section):
                # Only override if not explicitly set on command line
                arg_name = key.replace('-', '_')
                if not hasattr(args, arg_name) or getattr(args, arg_name) is None:
                    setattr(args, arg_name, value)
    
    return args

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Cubestat - System monitoring with horizon charts")
    configure_argparse(parser)
    args = parser.parse_args()
    
    # Load configuration file if specified
    args = load_config(args)
    
    # Continue with application initialization...
```

## Step 7: Add output options

Add options to control output format and destination:

```python
def configure_argparse(parser):
    """Configure command line arguments."""
    # Existing arguments...
    
    # Add output format and destination options
    output_group = parser.add_argument_group('Output Options')
    output_group.add_argument(
        '--output',
        type=str,
        choices=['terminal', 'csv', 'json', 'influxdb'],
        default='terminal',
        help='Output format. Default: terminal'
    )
    output_group.add_argument(
        '--output-file',
        type=str,
        help='File to write output to (for csv/json formats)'
    )
    output_group.add_argument(
        '--influxdb-url',
        type=str,
        help='InfluxDB URL (for influxdb output)'
    )
    output_group.add_argument(
        '--influxdb-db',
        type=str,
        default='cubestat',
        help='InfluxDB database name (for influxdb output)'
    )
```

## Step 8: Add options with dependencies

Some options may depend on others:

```python
def configure_argparse(parser):
    """Configure command line arguments."""
    # Existing arguments...
    
    # Add feature flags
    feature_group = parser.add_argument_group('Feature Flags')
    feature_group.add_argument(
        '--enable-gpu',
        action='store_true',
        help='Enable GPU monitoring'
    )
    feature_group.add_argument(
        '--gpu-poll-interval',
        type=int,
        default=2000,
        help='GPU polling interval in milliseconds (requires --enable-gpu)'
    )
    
def validate_args(args):
    """Validate command line arguments."""
    # Check for option dependencies
    if args.gpu_poll_interval != 2000 and not args.enable_gpu:
        print("Warning: --gpu-poll-interval has no effect without --enable-gpu")
    
    # Return validated args
    return args
```

## Step 9: Add help and documentation

Add clear help text and examples:

```python
def configure_argparse(parser):
    """Configure command line arguments."""
    # Add examples section to help
    parser.formatter_class = argparse.RawDescriptionHelpFormatter
    parser.description = """
    Cubestat - System monitoring with horizon charts.
    
    Examples:
      cubestat                          # Run with default settings
      cubestat --refresh-rate 500       # Refresh twice per second
      cubestat --view all               # Show all metrics at once
      cubestat --cpu show --mem hide    # Show CPU metrics, hide memory metrics
    """
    
    # Existing arguments...
```

## Step 10: Add arguments for metric collections

Group related metrics with argument groups:

```python
def configure_argparse(parser):
    """Configure command line arguments."""
    # Create argument groups for related metrics
    system_group = parser.add_argument_group('System Metrics')
    network_group = parser.add_argument_group('Network Metrics')
    gpu_group = parser.add_argument_group('GPU Metrics')
    
    # Configure system metrics
    cpu_metric.configure_argparse(system_group)
    memory_metric.configure_argparse(system_group)
    swap_metric.configure_argparse(system_group)
    
    # Configure network metrics
    network_metric.configure_argparse(network_group)
    
    # Configure GPU metrics
    gpu_metric.configure_argparse(gpu_group)
```

## Advanced Command-Line Handling

### Subcommands

For more complex applications, use subcommands:

```python
def configure_argparse():
    """Configure command line arguments with subcommands."""
    parser = argparse.ArgumentParser(description="Cubestat - System monitoring with horizon charts")
    
    # Add global arguments
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug output'
    )
    
    # Add subcommands
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Monitor command (default)
    monitor_parser = subparsers.add_parser('monitor', help='Monitor system metrics (default)')
    configure_monitor_args(monitor_parser)
    
    # Record command (record metrics to file)
    record_parser = subparsers.add_parser('record', help='Record metrics to file')
    configure_record_args(record_parser)
    
    # Analyze command (analyze recorded metrics)
    analyze_parser = subparsers.add_parser('analyze', help='Analyze recorded metrics')
    configure_analyze_args(analyze_parser)
    
    return parser
```

### Environment variable overrides

Allow environment variables to override command-line arguments:

```python
def get_args():
    """Parse command line arguments with environment variable fallbacks."""
    parser = configure_argparse()
    args = parser.parse_args()
    
    # Check environment variables for overrides
    if os.environ.get('CUBESTAT_DEBUG') and not args.debug:
        args.debug = True
        
    if os.environ.get('CUBESTAT_REFRESH_RATE') and not hasattr(args, 'refresh_rate'):
        try:
            args.refresh_rate = int(os.environ.get('CUBESTAT_REFRESH_RATE'))
        except ValueError:
            print(f"Warning: Invalid CUBESTAT_REFRESH_RATE: {os.environ.get('CUBESTAT_REFRESH_RATE')}")
    
    return args
```

## Next Steps

- [Implementing Proper Logging](./implementing-logging.md)
- [Custom Data Exporters](./custom-data-exporters.md)
- [Integration with External Tools](./integration-with-external-tools.md)