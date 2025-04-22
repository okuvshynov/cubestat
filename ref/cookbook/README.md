# Cubestat Cookbook

Welcome to the Cubestat Cookbook! This collection of tutorials and guides will help you accomplish common tasks when working with the Cubestat codebase.

## Tutorials

### Core Development
1. [Adding a New Metric](./adding-a-new-metric.md) - Learn how to create and register new system metrics
2. [Implementing Platform-Specific Code](./implementing-platform-specific-code.md) - Guide for adding support for new platforms
3. [Building Custom Visualizations](./building-custom-visualizations.md) - Create new ways to visualize metrics

### Code Quality and Modernization
4. [Adding Type Hints](./adding-type-hints.md) - How to add type hints to legacy code
5. [Creating Unit Tests](./creating-unit-tests.md) - Guide for adding effective tests
6. [Implementing Proper Logging](./implementing-logging.md) - Improve error handling with proper logging

### Performance and Testing
7. [Creating Load Generators](./creating-load-generators.md) - Scripts to test metric collectors
8. [Optimizing Data Collection](./optimizing-data-collection.md) - Make metrics collection more efficient
9. [Cross-Platform Testing](./cross-platform-testing.md) - Ensure code works on multiple platforms

### Extensions
10. [Adding Command-Line Options](./adding-command-line-options.md) - Extend the CLI interface
11. [Custom Data Exporters](./custom-data-exporters.md) - Export metrics data to external systems
12. [Integration with External Tools](./integration-with-external-tools.md) - Connect Cubestat with other tools

## Usage

Each tutorial is designed to be self-contained with step-by-step instructions. Choose the tutorial that matches your task and follow along!

```bash
# Common setup for all tutorials
pip install -e .
# For NVIDIA GPU support
pip install -e .[cuda]
```

## Contributing

Found a missing recipe? Have improvements to suggest? Feel free to contribute by adding new tutorials or enhancing existing ones. Check the [Development Guide](/ref/Development%20Guide.md) for contribution guidelines.