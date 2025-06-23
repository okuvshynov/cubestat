"""TUI transformer - converts standardized names back to presenter-friendly format."""

from typing import Dict, Any
from .base_transformer import MetricTransformer


class TUITransformer(MetricTransformer):
    """Transformer for Terminal UI output format."""
    
    def transform(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform standardized metric names back to the format expected by presenters.
        
        This maintains backward compatibility with the existing presenter implementations.
        
        Args:
            metrics: Dictionary of metrics in standardized format
        
        Returns:
            Dictionary with presenter-friendly keys
        """
        transformed = {}
        
        # Memory metrics
        if "memory.system.total.used.percent" in metrics:
            transformed["used_percent"] = metrics["memory.system.total.used.percent"]
        if "memory.system.total.used.bytes" in metrics:
            transformed["used_bytes"] = metrics["memory.system.total.used.bytes"]
        if "memory.system.wired.bytes" in metrics:
            transformed["wired_bytes"] = metrics["memory.system.wired.bytes"]
        if "memory.system.mapped.bytes" in metrics:
            transformed["mapped_bytes"] = metrics["memory.system.mapped.bytes"]
            
        # Network metrics
        if "network.total.rx.bytes_per_sec" in metrics:
            transformed["rx_bytes_per_sec"] = metrics["network.total.rx.bytes_per_sec"]
        if "network.total.tx.bytes_per_sec" in metrics:
            transformed["tx_bytes_per_sec"] = metrics["network.total.tx.bytes_per_sec"]
            
        # Disk metrics
        if "disk.total.read.bytes_per_sec" in metrics:
            transformed["disk_read"] = metrics["disk.total.read.bytes_per_sec"]
        if "disk.total.write.bytes_per_sec" in metrics:
            transformed["disk_write"] = metrics["disk.total.write.bytes_per_sec"]
            
        # Power metrics
        if "power.component.total.consumption.watts" in metrics:
            transformed["total_power"] = metrics["power.component.total.consumption.watts"]
        if "power.component.cpu.consumption.watts" in metrics:
            transformed["cpu_power"] = metrics["power.component.cpu.consumption.watts"]
        if "power.component.gpu.consumption.watts" in metrics:
            transformed["gpu_power"] = metrics["power.component.gpu.consumption.watts"]
        if "power.component.ane.consumption.watts" in metrics:
            transformed["ane_power"] = metrics["power.component.ane.consumption.watts"]
            
        # Swap metrics
        if "swap.total.used.bytes" in metrics:
            transformed["used_bytes"] = metrics["swap.total.used.bytes"]
            
        # Pass through any unrecognized metrics (for collectors not yet migrated)
        for key, value in metrics.items():
            # If it's not a standardized metric name, pass it through as-is
            if "." not in key:
                transformed[key] = value
        
        return transformed
    
    def should_include_metric(self, metric_name: str) -> bool:
        """
        Include metrics that presenters expect.
        
        Args:
            metric_name: Standardized metric name
            
        Returns:
            True if the metric should be included
        """
        # During migration, include everything
        # Later we can be more selective
        return True