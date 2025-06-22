import psutil
from typing import Any, Dict

from cubestat.common import RateReader
from cubestat.collectors.base_collector import BaseCollector
from cubestat.metrics_registry import collector_registry


class DiskCollector(BaseCollector):
    """Base disk I/O collector."""
    
    @classmethod
    def collector_id(cls) -> str:
        return 'disk'


@collector_registry.register('darwin')
class MacOSDiskCollector(DiskCollector):
    """macOS-specific disk I/O collector."""
    
    def collect(self, context: Dict[str, Any]) -> Dict[str, float]:
        return {
            'disk_read': context['disk']['rbytes_per_s'],
            'disk_write': context['disk']['wbytes_per_s']
        }


@collector_registry.register('linux')
class LinuxDiskCollector(DiskCollector):
    """Linux-specific disk I/O collector."""
    
    def __init__(self):
        self.rate_reader = None
    
    def configure(self, config: Dict[str, Any]) -> 'LinuxDiskCollector':
        self.rate_reader = RateReader(config.get('refresh_ms', 200))
        return self
    
    def collect(self, context: Dict[str, Any]) -> Dict[str, float]:
        disk_io = psutil.disk_io_counters()
        return {
            'disk_read': self.rate_reader.next('disk_read', disk_io.read_bytes),
            'disk_write': self.rate_reader.next('disk_write', disk_io.write_bytes)
        }