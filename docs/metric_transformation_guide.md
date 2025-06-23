# Metric Transformation Guide

This guide documents the process of migrating metrics to the standardized naming schema.

## Overview

The transformation system allows collectors to output standardized metric names while maintaining backward compatibility with existing presenters through transformers.

## Architecture

```
Collector → Standardized Names → Transformer → Presenter
```

1. **Collectors** return standardized metric names directly from `collect()`
2. **Transformers** convert between formats:
   - `CSVTransformer`: Preserves standardized names for scripting
   - `TUITransformer`: Converts to presenter-expected format
3. **MetricAdapter** orchestrates the flow: collector → transformer → presenter

## Migration Pattern

### Step 1: Update Collector

Modify the `collect()` method to return standardized names:

```python
# Before
def collect(self, context: Dict[str, Any]) -> Dict[str, float]:
    vm = psutil.virtual_memory()
    return {
        "used_percent": vm.percent,
        "used_bytes": vm.used,
        "wired_bytes": vm.wired,
    }

# After
def collect(self, context: Dict[str, Any]) -> Dict[str, float]:
    vm = psutil.virtual_memory()
    return {
        "memory.system.total.used.percent": vm.percent,
        "memory.system.total.used.bytes": vm.used,
        "memory.system.wired.bytes": vm.wired,
    }
```

### Step 2: Update TUI Transformer

Add mappings for the new standardized names in `tui_transformer.py`:

```python
# Memory metrics
if "memory.system.total.used.percent" in metrics:
    transformed["used_percent"] = metrics["memory.system.total.used.percent"]
```

### Step 3: Remove Metric Adapter Overrides

**CRITICAL**: Remove any `read()` method overrides in the metric adapter:

```python
# Before - WRONG (bypasses transformer)
class MemoryMetricAdapter(MetricAdapter):
    def read(self, context: Dict[str, Any]) -> Dict[str, float]:
        raw_data = self.collector.collect(context)
        return self.presenter.process_data(raw_data)  # Skips transformer!

# After - CORRECT (uses base class implementation)
class MemoryMetricAdapter(MetricAdapter):
    """Memory metric adapter handling data processing."""
    # No read() override - uses MetricAdapter.read() which includes transformer
```

### Step 4: Test

Create a test script to verify the transformation:

```python
# Get collector and test
collector = collector_registry.get_instance(system, "memory")
standardized_data = collector.collect({})
print("Standardized:", standardized_data)

# Transform and verify
transformer = TUITransformer()
tui_data = transformer.transform(standardized_data)
print("TUI format:", tui_data)

# Test end-to-end
from cubestat.metrics.memory import ram_metric_macos
metric = ram_metric_macos()
result = metric.read({})
print("Final result:", result)
```

## Naming Schema Reference

### Memory
- `memory.system.total.used.percent`
- `memory.system.total.used.bytes`
- `memory.system.wired.bytes` (macOS)
- `memory.system.mapped.bytes` (Linux)

### Network
- `network.total.rx.bytes_per_sec`
- `network.total.tx.bytes_per_sec`
- `network.interface.<name>.rx.bytes_per_sec`
- `network.interface.<name>.tx.bytes_per_sec`

### Disk
- `disk.total.read.bytes_per_sec`
- `disk.total.write.bytes_per_sec`
- `disk.device.<name>.read.bytes_per_sec`
- `disk.device.<name>.write.bytes_per_sec`

### CPU
- `cpu.<cluster>.<index>.core.<core>.utilization.percent`
- `cpu.total.utilization.percent`
- `cpu.total.count`

### GPU
- `gpu.<vendor>.<index>.compute.utilization.percent`
- `gpu.<vendor>.<index>.memory.used.bytes`
- `gpu.<vendor>.<index>.memory.total.bytes`
- `gpu.total.count`

### Power
- `power.component.total.consumption.watts`
- `power.component.cpu.consumption.watts`
- `power.component.gpu.consumption.watts`
- `power.component.ane.consumption.watts`

## Migration Order

1. ✅ Memory (completed - pilot)
2. Disk (simple, similar to memory)
3. Network (simple, test interface naming)
4. Power (test component hierarchy)
5. Swap (single value, simplest)
6. GPU (complex multi-instance)
7. CPU (most complex, needs flattening)

## Common Issues

### Issue: Metric Not Showing in TUI
**Symptom**: Collector works, transformer works, but metric doesn't appear in cubestat
**Cause**: Metric adapter overriding `read()` method and bypassing transformer
**Solution**: Remove `read()` override from metric adapter class

### Issue: Wrong Keys in Presenter
**Symptom**: Presenter receives standardized names instead of legacy names
**Cause**: Transformer not being called
**Solution**: Ensure MetricAdapter base class `read()` method is used

### Issue: Collector Import Errors
**Symptom**: Import errors when BaseCollector interface changes
**Cause**: Breaking changes to base collector
**Solution**: Use simple approach - `collect()` returns standardized names directly

## Testing Checklist

For each migrated metric:
- [ ] Collector returns standardized names
- [ ] TUI transformer maps standardized → legacy names  
- [ ] Metric adapter has no `read()` override
- [ ] End-to-end test: `metric.read({})` returns presenter-formatted data
- [ ] Manual test: metric appears correctly in cubestat TUI

## Notes

- During migration, untransformed metrics pass through unchanged
- The TUI transformer maintains backward compatibility
- CSV output will use standardized names
- Future outputs (JSON, Prometheus) can create their own transformers
- Non-migrated collectors continue to work as before