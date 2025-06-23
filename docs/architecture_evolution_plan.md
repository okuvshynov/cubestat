# Cubestat Architecture Evolution Plan

## Vision
Transform cubestat from a terminal-only monitoring tool into a flexible metrics collection and presentation framework, where the current horizon chart format becomes just one of many output options.

## Current State Analysis

### Metric Naming Inconsistencies
After completing the collector/presenter refactoring, we've identified several naming inconsistencies across collectors:
- **Structure**: CPU uses nested objects while others use flat dictionaries
- **Units**: Inconsistent inclusion (e.g., `used_bytes` vs `disk_read`)
- **Percentages**: `used_percent` vs `vram_used_percent` vs `utilization`
- **Multi-instance**: Different patterns for multiple devices (CPUs, GPUs)

These inconsistencies make it challenging to build reliable tooling and scripts on top of cubestat.

## Phase 0: Metric Naming Standardization & CSV Output (1-2 weeks)

### Goals
1. Establish consistent metric naming schema across all collectors
2. Implement transformation layer for output-specific formatting
3. Add CSV output as first alternative format
4. Learn from implementation before larger architectural changes

### Metric Naming Schema

#### Standard Format
```
<component>.<type>.<instance>.<attribute>.<unit>
```

#### Examples
- `cpu.efficiency.0.core.2.utilization.percent`
- `cpu.performance.0.core.1.utilization.percent`
- `gpu.nvidia.0.compute.utilization.percent`
- `gpu.nvidia.0.memory.used.bytes`
- `gpu.nvidia.0.memory.total.bytes`
- `network.interface.en0.rx.bytes_per_sec`
- `network.interface.en0.tx.bytes_per_sec`
- `memory.system.total.used.percent`
- `memory.system.total.used.bytes`
- `disk.device.disk0.read.bytes_per_sec`
- `power.component.cpu.consumption.watts`
- `power.component.total.consumption.watts`

### Transform Architecture

```
┌─────────────┐     ┌──────────────┐     ┌───────────────┐     ┌──────────────┐
│  Collectors │────▶│ Standardizer │────▶│ Transformer  │────▶│    Output    │
└─────────────┘     └──────────────┘     └───────────────┘     └──────────────┘
                           │                      │
                    Normalize to            Transform for
                    standard schema          output format
```

### Implementation Details

#### 1. Update BaseCollector
```python
class BaseCollector(ABC):
    @abstractmethod
    def collect_raw(self) -> Dict[str, Any]:
        """Collect raw data in platform-specific format"""
        pass
    
    @abstractmethod
    def standardize(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert to standard metric naming schema"""
        pass
    
    def collect(self) -> Dict[str, Any]:
        """Public API: returns standardized metrics"""
        raw = self.collect_raw()
        return self.standardize(raw)
```

#### 2. Create Transform Interface
```python
class MetricTransformer(ABC):
    """Transforms standardized metrics to output-specific format"""
    
    @abstractmethod
    def transform(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Transform metrics for specific output format"""
        pass

class CSVTransformer(MetricTransformer):
    """Preserves hierarchical names for scripting"""
    def transform(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        # Returns metrics as-is with dot notation
        return metrics

class TUITransformer(MetricTransformer):
    """Human-friendly names for terminal display"""
    def transform(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        # Converts to current display format
        # cpu.efficiency.0.core.2.utilization.percent -> for presenter
        return self._to_display_format(metrics)
```

#### 3. CSV Output Implementation
```python
class CSVOutput:
    def __init__(self, file_path: Optional[str] = None):
        self.file_path = file_path or sys.stdout
        self.first_write = True
    
    def write(self, timestamp: float, metrics: Dict[str, Any]):
        # Write header on first write
        # Append metrics with timestamp
        pass
```

### CLI Usage
```bash
# Stream to stdout
cubestat --output csv

# Write to file
cubestat --output csv --output-file system-metrics.csv

# Default behavior unchanged
cubestat  # Shows horizon charts as normal
```

### Benefits of This Approach
1. **Minimal Risk**: Small, focused changes
2. **Immediate Value**: CSV output for scripting/analysis
3. **Learning Opportunity**: Understand requirements before larger changes
4. **Foundation**: Establishes patterns for future outputs
5. **Backward Compatible**: Existing TUI behavior unchanged

## Phase 1: Output Abstraction (2-3 weeks)

### Goals
- Extract output interface based on CSV learnings
- Add JSON output format
- Support multiple simultaneous outputs
- Create output configuration system

### High-Level Design
- Generic output interface
- Output manager for multiple outputs
- Configuration for output options
- Real-time vs batch considerations

## Phase 2: Storage Abstraction (3-4 weeks)

### Goals
- Separate data storage from collection
- Add persistent storage options
- Enable historical data queries
- Support different retention policies

### High-Level Components
- Storage interface
- Memory storage (current)
- SQLite storage
- Query API for historical data

## Phase 3: Advanced Features (4-6 weeks)

### Potential Features
- HTTP API for remote access
- Daemon mode
- Metric aggregation/transformation
- Alerting system
- Plugin architecture

### Considerations
- Security (authentication, encryption)
- Performance at scale
- Configuration management
- Cross-platform compatibility

## Success Criteria

### Phase 0 Success Metrics
1. All collectors output standardized metric names
2. CSV output works reliably
3. No performance regression
4. Backward compatibility maintained
5. Clear documentation for metric schema

## Technical Decisions

### Why Start with CSV?
1. **Simple**: No complex dependencies
2. **Useful**: Immediate value for users
3. **Educational**: Learn requirements with minimal risk
4. **Scriptable**: Enables automation and analysis

### Transformer Pattern Benefits
1. **Separation of Concerns**: Collection vs presentation
2. **Flexibility**: Easy to add new output formats
3. **Maintainability**: Changes isolated to specific transformers
4. **Testability**: Each transformer can be tested independently

## Migration Notes
- Current users see no changes unless they opt-in
- Gradual migration path for each component
- Feature flags for experimental features
- Comprehensive testing at each phase

This incremental approach allows us to deliver value quickly while building toward the larger vision of a flexible metrics framework.