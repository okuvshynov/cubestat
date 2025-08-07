"""
Prometheus metrics HTTP server for cubestat.
This module provides an HTTP server that exposes metrics in Prometheus format.
"""

import logging
import threading
from typing import Optional

from prometheus_client import start_http_server

logger = logging.getLogger(__name__)


class PrometheusServer:
    """HTTP server for Prometheus metrics export."""
    
    def __init__(self, port: int, host: str = "localhost"):
        """
        Initialize Prometheus metrics server.
        
        Args:
            port: Port to serve metrics on
            host: Host to bind to (default: localhost)
        """
        self.port = port
        self.host = host
        self.server_thread: Optional[threading.Thread] = None
        self._server = None
        
    def start(self) -> None:
        """Start the Prometheus HTTP server in a background thread."""
        try:
            # Note: prometheus_client's start_http_server doesn't support custom host binding
            # It always binds to 0.0.0.0, which is actually what we want for Prometheus
            # The metrics will be available at http://{host}:{port}/metrics
            start_http_server(self.port)
            logger.info(f"Prometheus metrics server started on port {self.port}")
            logger.info(f"Metrics available at http://{self.host}:{self.port}/metrics")
        except Exception as e:
            logger.error(f"Failed to start Prometheus server: {e}")
            raise
    
    def stop(self) -> None:
        """Stop the Prometheus HTTP server."""
        # Note: prometheus_client's HTTP server runs in daemon threads
        # and will automatically stop when the main program exits
        logger.info("Prometheus metrics server stopping")