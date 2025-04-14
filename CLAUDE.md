# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands
- Install: `pip install -e .` or `pip install -e .[cuda]` for NVIDIA GPU support
- Run tests: `python -m unittest discover`
- Run single test: `python -m unittest cubestat.tests.test_data_manager`

## Code Style
- File/function/variable naming: snake_case (e.g., `data_manager.py`, `get_metrics`)
- Class naming: CamelCase (e.g., `DataManager`) 
- No explicit type hints in existing codebase
- Imports: standard library first, then project imports
- Prefer inheritance for metrics (extend `base_metric.BaseMetric`)
- Platform-specific implementations in separate modules
- Error handling: Keep minimal as per existing codebase
- Documentation: Follow existing minimal docstring style
- Support cross-platform (macOS, Linux) when implementing features
- Main entry point is `cubestat.cubestat:main`