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
            
        # CPU metrics - complex transformation maintaining cluster grouping order
        cpu_clusters = {}
        
        # First pass: collect all CPU metrics by cluster
        for key, value in metrics.items():
            if key.startswith("cpu.") and key != "cpu.total.count":
                parts = key.split(".")
                if len(parts) >= 7 and parts[3] == "core":
                    # Individual core: cpu.performance.0.core.2.utilization.percent
                    cluster_name = parts[1].capitalize()
                    cluster_index = parts[2]
                    core_id = parts[4]
                    cluster_key = f"{cluster_name}.{cluster_index}"
                    
                    if cluster_key not in cpu_clusters:
                        cpu_clusters[cluster_key] = {"cores": {}, "total_key": None, "total_value": None}
                    
                    cpu_clusters[cluster_key]["cores"][core_id] = value
                    
                elif len(parts) >= 6 and parts[3] == "total":
                    # Cluster total: cpu.performance.0.total.utilization.percent
                    cluster_name = parts[1].capitalize()
                    cluster_index = parts[2]
                    cluster_key = f"{cluster_name}.{cluster_index}"
                    
                    if cluster_key not in cpu_clusters:
                        cpu_clusters[cluster_key] = {"cores": {}, "total_key": None, "total_value": None}
                    
                    cpu_clusters[cluster_key]["total_key"] = key
                    cpu_clusters[cluster_key]["total_value"] = value
        
        # Second pass: build ordered output (cluster total, then its cores)
        # Sort clusters by minimum CPU ID to preserve original order (Performance cores typically have lower IDs)
        def cluster_sort_key(item):
            cluster_key, cluster_data = item
            if cluster_data["cores"]:
                return min(int(core_id) for core_id in cluster_data["cores"].keys())
            return float('inf')
        
        for cluster_key, cluster_data in sorted(cpu_clusters.items(), key=cluster_sort_key):
            cluster_name = cluster_key.split(".")[0]
            
            # Add cluster total first
            if cluster_data["total_value"] is not None:
                core_count = len(cluster_data["cores"])
                cluster_title = f"[{core_count}] {cluster_name} total CPU util %"
                transformed[cluster_title] = cluster_data["total_value"]
            
            # Then add individual cores in order
            for core_id in sorted(cluster_data["cores"].keys(), key=int):
                cpu_title = f"{cluster_name} CPU {core_id} util %"
                transformed[cpu_title] = cluster_data["cores"][core_id]
            
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