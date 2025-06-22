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

## Code Style
- File/function/variable naming: snake_case (e.g., `data_manager.py`, `get_metrics`)
- Class naming: CamelCase for primary classes (e.g., `DataManager`), snake_case for metrics 
- Add type hints to all new code and when refactoring existing code
- Imports: standard library first, then project imports
- **Metrics Architecture**: Use collector/presenter pattern (see Architecture section below)
- Platform-specific implementations in separate modules
- Error handling: Use try/except blocks with specific exceptions and logging
- Documentation: Add docstrings in Google style format to all functions and classes
- Logging: Use the logging module instead of print statements
- Support cross-platform (macOS, Linux) when implementing features
- Main entry point is `cubestat.cubestat:main`

## Architecture

### Collector/Presenter Pattern
New metrics should follow the collector/presenter architecture:

**Collectors** (`cubestat/collectors/`):
- Responsible for data collection from system APIs
- Platform-specific implementations (e.g., `MacOSCPUCollector`, `LinuxCPUCollector`)
- Return standardized data format
- Handle platform differences (psutil vs system context vs /proc files)

**Presenters** (`cubestat/presenters/`):
- Handle UI concerns: display modes, formatting, filtering
- Process collector data into display format
- Manage hotkeys and command-line arguments
- Platform-agnostic display logic

**Metric Adapters** (`cubestat/metrics/`):
- Bridge between new architecture and existing metric system
- Coordinate collector and presenter
- Maintain backward compatibility with hotkey system

### Example Structure
```
cubestat/collectors/memory_collector.py   # Data collection
cubestat/presenters/memory_presenter.py   # UI/formatting  
cubestat/metrics/memory.py                # Coordination
```

### Platform-Specific Guidelines
- **macOS-only metrics** (power, accel): No Linux implementation to avoid confusion
- **Cross-platform metrics** (CPU, memory, network): Platform-specific collectors
- **Graceful degradation**: Clear absence better than misleading zero values