from typing import Any, Dict

import psutil

from cubestat.collectors.base_collector import BaseCollector
from cubestat.common import RateReader
from cubestat.metrics_registry import collector_registry


class NetworkCollector(BaseCollector):
    """Base network collector."""

    @classmethod
    def collector_id(cls) -> str:
        return "network"


@collector_registry.register("darwin")
class MacOSNetworkCollector(NetworkCollector):
    """macOS-specific network collector using system context."""

    def collect(self, context: Dict[str, Any]) -> Dict[str, float]:
        """Collect network rates from macOS system context."""
        network_data = context.get("network", {})
        return {
            "rx_bytes_per_sec": network_data.get("ibyte_rate", 0.0),
            "tx_bytes_per_sec": network_data.get("obyte_rate", 0.0),
        }


@collector_registry.register("linux")
class LinuxNetworkCollector(NetworkCollector):
    """Linux-specific network collector using psutil with rate calculation."""

    def __init__(self):
        self.rate_reader = None

    def configure(self, config) -> "LinuxNetworkCollector":
        # Handle both Dict and Namespace objects
        if hasattr(config, "get"):
            refresh_ms = config.get("refresh_ms", 200)
        else:
            refresh_ms = getattr(config, "refresh_ms", 200)
        self.rate_reader = RateReader(refresh_ms)
        return self

    def collect(self, context: Dict[str, Any]) -> Dict[str, float]:
        """Collect network rates using psutil and rate calculation."""
        if self.rate_reader is None:
            # Fallback if not configured
            self.rate_reader = RateReader(200)

        net_io = psutil.net_io_counters()
        return {
            "rx_bytes_per_sec": self.rate_reader.next("network_rx", net_io.bytes_recv),
            "tx_bytes_per_sec": self.rate_reader.next("network_tx", net_io.bytes_sent),
        }
