# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands
- Install: `pip install -e .` or `pip install -e .[cuda]` for NVIDIA GPU support
- Install dev dependencies: `pip install -r requirements-dev.txt`
- Run tests: `python -m unittest discover`
- Run single test: `python -m unittest cubestat.tests.test_data_manager`
- Type check: `mypy cubestat`
- Lint: `ruff check cubestat`
- Format: `ruff format cubestat`
- Run TUI mode: `python -m cubestat.cubestat`
- Run CSV export: `python -m cubestat.cubestat --csv`

## Code Style
- File/function/variable naming: snake_case (e.g., `data_manager.py`, `get_metrics`)
- Class naming: CamelCase for primary classes (e.g., `DataManager`), snake_case for metrics 
- Add type hints to all new code and when refactoring existing code
- Imports: standard library first, then project imports
- **Metrics Architecture**: Use collector/presenter/transformer pattern (see Architecture section below)
- **Metric Naming**: Use standardized `component.type.instance.attribute.unit` format
- Platform-specific implementations in separate modules
- Error handling: Use try/except blocks with specific exceptions and logging
- Documentation: Add docstrings in Google style format to all functions and classes
- Logging: Use the logging module instead of print statements
- Support cross-platform (macOS, Linux) when implementing features
- Main entry point is `cubestat.cubestat:main`

## Architecture

### Collector/Presenter/Transformer Pattern
All metrics follow the collector/presenter/transformer architecture with standardized naming:

**Collectors** (`cubestat/collectors/`):
- Responsible for data collection from system APIs
- Platform-specific implementations (e.g., `MacOSCPUCollector`, `LinuxCPUCollector`)
- **Return standardized metric names**: `component.type.instance.attribute.unit`
- Handle platform differences (psutil vs system context vs /proc files)

**Transformers** (`cubestat/transformers/`):
- Convert between standardized names and output-specific formats
- **TUITransformer**: Converts standardized names to presenter-expected format
- **CSVTransformer**: Preserves standardized names for export
- Enable multiple output formats without changing collectors

**Presenters** (`cubestat/presenters/`):
- Handle UI concerns: display modes, formatting, filtering
- Process transformed data into final display format
- Manage hotkeys and command-line arguments
- Platform-agnostic display logic

**Metric Adapters** (`cubestat/metrics/`):
- Bridge between new architecture and existing metric system
- Coordinate collector, transformer, and presenter
- **IMPORTANT**: Do NOT override read() method - use base implementation for transformer flow

### Data Flow
```
Collector → Standardized Names → Transformer → Presenter → Display
    ↓              ↓                  ↓           ↓         ↓
Raw System   component.type.     TUI: old     Format    TUI Chart
   Data      instance.attr.unit  CSV: std     Values    CSV Output
```

### Example Structure
```
cubestat/collectors/memory_collector.py   # Data collection → standardized names
cubestat/transformers/tui_transformer.py  # TUI format conversion
cubestat/transformers/csv_transformer.py  # CSV format (pass-through)
cubestat/presenters/memory_presenter.py   # UI/formatting  
cubestat/metrics/memory.py                # Coordination (no read() override)
```

### Standardized Naming Examples
- `memory.system.total.used.percent`
- `cpu.performance.0.core.2.utilization.percent`
- `gpu.nvidia.0.utilization.percent`
- `power.component.cpu.consumption.watts`
- `network.total.rx.bytes_per_sec`

### Output Modes
**TUI Mode (default)**:
- Interactive terminal interface with horizon charts
- Uses TUITransformer for backward-compatible display names
- Requires curses and 256-color terminal

**CSV Export Mode (`--csv`)**:
- Non-interactive streaming CSV output to stdout
- Uses CSVTransformer to preserve standardized metric names  
- Perfect for monitoring systems, scripts, and data analysis
- Format: `timestamp,metric,value`
- Example: `1750693377.593887,cpu.performance.0.core.0.utilization.percent,26.7591`

### Platform-Specific Guidelines
- **macOS-only metrics** (power, accel): No Linux implementation to avoid confusion
- **Cross-platform metrics** (CPU, memory, network): Platform-specific collectors
- **Graceful degradation**: Clear absence better than misleading zero values