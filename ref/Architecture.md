# Cubestat Architecture

Cubestat is a terminal-based system monitoring tool that displays metrics using horizon charts for high information density. This document provides an overview of the system architecture and the interaction between various components.

## High-Level Architecture

Cubestat follows a modular architecture with several key components:

```
                ┌────────────────┐
                │    Cubestat    │
                │   (Main App)   │
                └────────┬───────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
┌────────▼─────────┐ ┌───▼────┐  ┌──────▼─────────┐
│  DataManager     │ │ Screen │  │  InputHandler  │
│ (Data Storage)   │ │(Output)│  │  (User Input)  │
└────────┬─────────┘ └───┬────┘  └──────┬─────────┘
         │               │               │
         └───────────────┼───────────────┘
                         │
                ┌────────▼───────┐
                │ Metrics Registry│
                └────────┬───────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
┌────────▼─────────┐ ┌───▼────┐  ┌──────▼─────────┐
│   CPU Metrics    │ │ Memory │  │    Network     │
│                  │ │ Metrics│  │    Metrics     │
└────────┬─────────┘ └───┬────┘  └──────┬─────────┘
         │               │               │
         └───────────────┼───────────────┘
                         │
                ┌────────▼───────┐
                │Platform Factory│
                └────────┬───────┘
                         │
                ┌────────┴───────┐
     ┌──────────┤  Platforms     ├──────────┐
     │          └────────────────┘          │
┌────▼─────┐                         ┌──────▼───┐
│  Linux   │                         │  macOS   │
└──────────┘                         └──────────┘
```

## Component Overview

### Main Components

1. **Cubestat (Main Application)**: 
   - Entry point and orchestrator
   - Initializes all components
   - Runs the main loop for data collection and rendering

2. **DataManager**:
   - Manages time series data storage
   - Buffers data for all metrics
   - Provides slicing and access methods

3. **Screen**:
   - Handles terminal rendering using curses
   - Draws horizon charts, rulers, and labels

4. **InputHandler**:
   - Processes keyboard input
   - Enables interactive mode switching
   - Manages scrolling and navigation

### Metrics System

1. **Metrics Registry**:
   - Dynamically loads and registers metrics
   - Provides metrics configuration
   - Manages metrics lifecycle

2. **Metrics**:
   - Various metric implementations (CPU, GPU, Memory, etc.)
   - Each metric inherits from BaseMetric
   - Platform-specific metric implementations

### Platform Abstraction

1. **Platform Factory**:
   - Creates the appropriate platform implementation
   - Determines current OS and capabilities

2. **Platform Implementations**:
   - macOS: Uses powermetrics for data collection
   - Linux: Uses direct system calls and file parsing
   - Both implement consistent interfaces

## Data Flow

1. The main application initializes all components
2. Platform-specific implementation collects system metrics
3. Metrics are processed and normalized
4. DataManager stores the time series data
5. Screen renders the data as horizon charts
6. InputHandler processes user input to adjust display
7. The cycle repeats at the specified refresh interval

## Threading Model

- The main thread handles rendering and user input
- A background thread runs platform-specific data collection
- Thread synchronization uses locks to prevent race conditions

## Extensibility

Cubestat is designed to be extensible:
- New metrics can be added by inheriting from BaseMetric
- New platforms can be supported by implementing the platform interface
- Display modes and formatting can be customized