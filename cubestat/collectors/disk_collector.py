from typing import Any, Dict, Optional

import psutil
from prometheus_client import Gauge

from cubestat.collectors.base_collector import BaseCollector
from cubestat.common import RateReader
from cubestat.metrics_registry import collector_registry


class DiskCollector(BaseCollector):
    """Base disk I/O collector."""
    
    @classmethod
    def collector_id(cls) -> str:
        return 'disk'


@collector_registry.register('darwin')
class MacOSDiskCollector(DiskCollector):
    """macOS-specific disk I/O collector."""
    
    def __init__(self):
        # Initialize Prometheus metrics
        self.disk_read_gauge: Optional[Gauge] = None
        self.disk_write_gauge: Optional[Gauge] = None
        self._init_prometheus_metrics()
    
    def _init_prometheus_metrics(self) -> None:
        """Initialize Prometheus Gauge metrics for disk I/O monitoring."""
        try:
            self.disk_read_gauge = Gauge(
                'disk_read_bytes_per_second',
                'Disk read throughput in bytes per second'
            )
            self.disk_write_gauge = Gauge(
                'disk_write_bytes_per_second',
                'Disk write throughput in bytes per second'
            )
        except Exception:
            # Gauges might already exist if collector is re-initialized
            self.disk_read_gauge = None
            self.disk_write_gauge = None
    
    def collect(self, context: Dict[str, Any]) -> Dict[str, float]:
        read_bytes_per_sec = context['disk']['rbytes_per_s']
        write_bytes_per_sec = context['disk']['wbytes_per_s']
        
        # Update Prometheus gauges
        if self.disk_read_gauge is not None:
            self.disk_read_gauge.set(read_bytes_per_sec)
        if self.disk_write_gauge is not None:
            self.disk_write_gauge.set(write_bytes_per_sec)
        
        return {
            'disk.total.read.bytes_per_sec': read_bytes_per_sec,
            'disk.total.write.bytes_per_sec': write_bytes_per_sec
        }


@collector_registry.register('linux')
class LinuxDiskCollector(DiskCollector):
    """Linux-specific disk I/O collector."""
    
    def __init__(self):
        self.rate_reader: Optional[RateReader] = None
        # Initialize Prometheus metrics
        self.disk_read_gauge: Optional[Gauge] = None
        self.disk_write_gauge: Optional[Gauge] = None
        self._init_prometheus_metrics()
    
    def _init_prometheus_metrics(self) -> None:
        """Initialize Prometheus Gauge metrics for disk I/O monitoring."""
        try:
            self.disk_read_gauge = Gauge(
                'disk_read_bytes_per_second',
                'Disk read throughput in bytes per second'
            )
            self.disk_write_gauge = Gauge(
                'disk_write_bytes_per_second',
                'Disk write throughput in bytes per second'
            )
        except Exception:
            # Gauges might already exist if collector is re-initialized
            self.disk_read_gauge = None
            self.disk_write_gauge = None
    
    def configure(self, config) -> 'LinuxDiskCollector':
        # Handle both Dict and Namespace objects
        if hasattr(config, 'get'):
            refresh_ms = config.get('refresh_ms', 200)
        else:
            refresh_ms = getattr(config, 'refresh_ms', 200)
        self.rate_reader = RateReader(refresh_ms)
        return self
    
    def collect(self, context: Dict[str, Any]) -> Dict[str, float]:
        disk_io = psutil.disk_io_counters()
        
        if self.rate_reader is None:
            # This shouldn't happen if configure() was called properly
            return {
                'disk.total.read.bytes_per_sec': 0.0,
                'disk.total.write.bytes_per_sec': 0.0
            }
        
        read_bytes_per_sec = self.rate_reader.next('disk_read', disk_io.read_bytes)
        write_bytes_per_sec = self.rate_reader.next('disk_write', disk_io.write_bytes)
        
        # Update Prometheus gauges
        if self.disk_read_gauge is not None:
            self.disk_read_gauge.set(read_bytes_per_sec)
        if self.disk_write_gauge is not None:
            self.disk_write_gauge.set(write_bytes_per_sec)
        
        return {
            'disk.total.read.bytes_per_sec': read_bytes_per_sec,
            'disk.total.write.bytes_per_sec': write_bytes_per_sec
        }