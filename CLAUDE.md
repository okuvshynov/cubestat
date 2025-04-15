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
- Prefer inheritance for metrics (extend `base_metric.BaseMetric`)
- Platform-specific implementations in separate modules
- Error handling: Use try/except blocks with specific exceptions and logging
- Documentation: Add docstrings in Google style format to all functions and classes
- Logging: Use the logging module instead of print statements
- Support cross-platform (macOS, Linux) when implementing features
- Main entry point is `cubestat.cubestat:main`