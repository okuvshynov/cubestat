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

## Advanced Example: CPU Metric Migration

The CPU metric was the most complex migration, involving hierarchical data flattening and ordering preservation.

### Original Structure (Complex)
```python
# Collector returned nested CPUCluster objects
{
  "clusters": [
    CPUCluster("Performance", [{"cpu": 0, "utilization": 70}, {"cpu": 1, "utilization": 60}]),
    CPUCluster("Efficiency", [{"cpu": 2, "utilization": 20}, {"cpu": 3, "utilization": 10}])
  ],
  "total_cpus": 4
}
```

### Standardized Format (Flat)
```python
{
  "cpu.performance.0.core.0.utilization.percent": 70.0,
  "cpu.performance.0.core.1.utilization.percent": 60.0,
  "cpu.performance.0.total.utilization.percent": 65.0,
  "cpu.efficiency.0.core.2.utilization.percent": 20.0,
  "cpu.efficiency.0.core.3.utilization.percent": 10.0,
  "cpu.efficiency.0.total.utilization.percent": 15.0,
  "cpu.total.count": 4
}
```

### TUI Display Format (Ordered)
```python
{
  "[2] Performance total CPU util %": 65.0,    # Cluster total first
  "Performance CPU 0 util %": 70.0,           # Individual cores follow
  "Performance CPU 1 util %": 60.0,
  "[2] Efficiency total CPU util %": 15.0,    # Next cluster total
  "Efficiency CPU 2 util %": 20.0,           # Its cores follow
  "Efficiency CPU 3 util %": 10.0
}
```

### Key Challenges Solved
1. **Hierarchical Flattening**: Converted nested cluster structure to flat dot-notation
2. **Display Ordering**: Maintained cluster grouping (total + cores) using custom sort
3. **Presenter Compatibility**: Updated presenter to handle both old and new formats
4. **Multi-Platform**: Works for macOS clusters and Linux single-cluster

### Transformer Logic Summary
```python
# 1. Parse standardized names into clusters
# 2. Group cores and totals by cluster
# 3. Sort clusters by minimum core ID (preserves P-core/E-core order)
# 4. Output cluster total, then its cores, repeat for next cluster
```

This pattern can be applied to other hierarchical metrics (GPU with multiple devices, etc.).

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

### CPU (Complex Hierarchical)
- `cpu.<cluster>.<cluster_index>.core.<core_id>.utilization.percent`
- `cpu.<cluster>.<cluster_index>.total.utilization.percent`
- `cpu.total.count`

**Examples:**
- `cpu.performance.0.core.2.utilization.percent` (P-Core 2 in cluster 0)
- `cpu.efficiency.0.total.utilization.percent` (E-Core cluster total)
- `cpu.cpu.0.core.1.utilization.percent` (Linux: Core 1 in single cluster)

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
2. ✅ Disk (completed - simple, similar to memory)
3. ✅ Network (completed - simple, interface naming)
4. ✅ CPU (completed - most complex, hierarchical flattening)
5. Power (test component hierarchy)
6. Swap (single value, simplest)
7. GPU (complex multi-instance)
8. Accel (simple single value)

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

### Issue: Wrong Display Ordering (Complex Metrics)
**Symptom**: Hierarchical metrics show incorrect grouping (e.g., all cores then all clusters)
**Cause**: Simple alphabetical sorting doesn't preserve logical grouping
**Solution**: Custom sorting logic in transformer (e.g., CPU clusters by minimum core ID)

### Issue: Presenter Expects Old Format
**Symptom**: Presenter crashes looking for old structure (e.g., "clusters" key)
**Cause**: Presenter designed for original collector format
**Solution**: Update presenter to handle both old and new flat formats

## Testing Checklist

For each migrated metric:
- [ ] Collector returns standardized names
- [ ] TUI transformer maps standardized → legacy names  
- [ ] Metric adapter has no `read()` override
- [ ] End-to-end test: `metric.read({})` returns presenter-formatted data
- [ ] Manual test: metric appears correctly in cubestat TUI
- [ ] **Complex metrics only**: Verify display ordering preserves logical grouping
- [ ] **Complex metrics only**: Update presenter if it expects old structure

## Notes

- During migration, untransformed metrics pass through unchanged
- The TUI transformer maintains backward compatibility
- CSV output will use standardized names
- Future outputs (JSON, Prometheus) can create their own transformers
- Non-migrated collectors continue to work as before