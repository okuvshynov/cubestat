# Core Components

Cubestat consists of several core components that work together to provide a comprehensive system monitoring experience. This document details these components and their interactions.

## Main Application (cubestat.py)

The `Cubestat` class in `cubestat.py` serves as the primary application controller:

- **Initialization**: Sets up the screen, data manager, and input handler
- **Reading Metrics**: Collects metrics from registered sources via the `do_read` method
- **Rendering**: Renders metrics data as horizon charts using the `render` method
- **Main Loop**: Orchestrates the continuous cycle of data collection, processing, and display

Key features:
- Supports display modes (view mode on/off/all)
- Handles horizontal and vertical scrolling
- Manages ruler intervals and time display
- Controls thread synchronization via locks

## Data Management (data.py)

The `DataManager` class in `data.py` manages time series data for all metrics:

- **Data Storage**: Uses collections.deque for efficient sliding window storage
- **Data Updates**: Handles new data points via the `update` method
- **Data Access**: Provides slicing and retrieval methods
- **Data Generation**: Yields data series for rendering

Key capabilities:
- Fixed-size buffer with configurable capacity
- Efficient slice access for viewport rendering
- Thread-safe operations

## Screen Rendering (screen.py)

The `Screen` class in `screen.py` handles all terminal output:

- **Curses Integration**: Uses the curses library for terminal manipulation
- **Chart Rendering**: Draws horizon charts with appropriate colors
- **Ruler Display**: Shows measurement scales and labels
- **Time Indicators**: Displays time references for data points

Key features:
- Handles window resizing
- Manages color palette and themes
- Provides optimized terminal rendering

## Input Handling (input.py)

The `InputHandler` class in `input.py` processes all user input:

- **Keyboard Events**: Captures and interprets key presses
- **Mode Switching**: Toggles between different display modes
- **Navigation**: Handles scrolling and position reset
- **Application Control**: Manages application exit

Supported keys:
- `q` - Quit the application
- `v` - Toggle view mode
- `c` - Change CPU display mode
- `g` - Change GPU display mode
- `d` - Toggle disk metrics display
- `n` - Toggle network metrics display
- `s` - Toggle swap metrics display
- `p` - Toggle power usage display
- Arrow keys - Scroll the display
- `0` - Reset scrolling position

## Colors and Themes (colors.py)

The `colors.py` module manages color handling:

- **Color Themes**: Defines different color schemes
- **ANSI Color**: Implements terminal color codes
- **Theme Selection**: Provides theme switching functionality

Supported themes:
- Standard color theme with gradient support
- Customizable color ranges for different metrics

## Common Utilities (common.py)

The `common.py` module provides shared utility functions:

- **Measurement Formatting**: Functions to format values with appropriate units
- **Display Modes**: Enums for various display modes
- **Rate Calculation**: Utilities for calculating rates from samples
- **Shared Constants**: Common constants used throughout the application

## Metrics Registry (metrics_registry.py)

The `metrics_registry.py` module manages metric registration and configuration:

- **Metric Registration**: Dynamically registers metrics from submodules
- **Argument Configuration**: Sets up command-line arguments for metrics
- **Metric Instantiation**: Creates metric instances based on configuration

Key features:
- Decorator-based registration system
- Dynamic metric loading
- Consistent configuration interface

## Component Interactions

These components interact in the following ways:

1. The main application initializes the screen, data manager, and input handler
2. Platform-specific code collects raw metrics data
3. Registered metrics process the raw data into formatted metrics
4. The data manager stores the processed metrics
5. The screen renders the stored metrics as horizon charts
6. The input handler processes user input to control the display
7. The cycle repeats at the specified refresh interval

This modular design allows for easy extension and customization of the application, with clear separation of concerns between components.