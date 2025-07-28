"""HTTP server module for exposing cubestat metrics as JSON."""

import json
import logging
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Dict, Optional


class MetricsHandler(BaseHTTPRequestHandler):
    """HTTP request handler for serving metrics data."""

    def __init__(self, data_manager, *args, **kwargs):
        self.data_manager = data_manager
        super().__init__(*args, **kwargs)

    def do_GET(self) -> None:
        """Handle GET requests for metrics endpoint."""
        if self.path == '/metrics':
            self._serve_metrics()
        else:
            self._send_404()

    def _serve_metrics(self) -> None:
        """Serve current metrics data as JSON."""
        try:
            # Convert data_manager.data_gen() output to JSON-serializable format
            metrics_data: Dict[str, Dict[str, Any]] = {}
            
            for group_name, title, series in self.data_manager.data_gen():
                if group_name not in metrics_data:
                    metrics_data[group_name] = {}
                
                # Convert deque to list and get current (latest) value
                series_list = list(series)
                current_value = series_list[-1] if series_list else None
                
                metrics_data[group_name][title] = {
                    'current_value': current_value,
                    'history': series_list,
                    'count': len(series_list)
                }

            response_data = {
                'timestamp': None,  # Will be filled by the platform context if needed
                'metrics': metrics_data
            }

            self._send_json_response(response_data)
            
        except Exception as e:
            logging.error(f"Error serving metrics: {e}")
            self._send_error_response(500, "Internal Server Error")

    def _send_json_response(self, data: Dict[str, Any]) -> None:
        """Send JSON response with appropriate headers."""
        response_json = json.dumps(data, indent=2)
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')  # Enable CORS
        self.send_header('Content-Length', str(len(response_json)))
        self.end_headers()
        
        self.wfile.write(response_json.encode('utf-8'))

    def _send_404(self) -> None:
        """Send 404 Not Found response."""
        self._send_error_response(404, "Not Found")

    def _send_error_response(self, code: int, message: str) -> None:
        """Send error response."""
        self.send_response(code)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write(message.encode('utf-8'))

    def log_message(self, format: str, *args) -> None:
        """Override to use Python logging instead of stderr."""
        logging.info(f"HTTP {self.address_string()} - {format % args}")


class HTTPMetricsServer:
    """HTTP server for serving cubestat metrics."""

    def __init__(self, host: str, port: int, data_manager) -> None:
        """Initialize HTTP server.
        
        Args:
            host: Host to bind to
            port: Port to listen on
            data_manager: DataManager instance containing metrics data
        """
        self.host = host
        self.port = port
        self.data_manager = data_manager
        self.server: Optional[HTTPServer] = None
        self.server_thread: Optional[threading.Thread] = None

    def start(self) -> None:
        """Start the HTTP server in a separate thread."""
        try:
            # Create handler class with data_manager bound
            handler_class = lambda *args, **kwargs: MetricsHandler(self.data_manager, *args, **kwargs)
            
            self.server = HTTPServer((self.host, self.port), handler_class)
            self.server_thread = threading.Thread(target=self.server.serve_forever, daemon=True)
            self.server_thread.start()
            
            logging.info(f"HTTP metrics server started on http://{self.host}:{self.port}/metrics")
            
        except Exception as e:
            logging.error(f"Failed to start HTTP server: {e}")
            raise

    def stop(self) -> None:
        """Stop the HTTP server."""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            if self.server_thread:
                self.server_thread.join()
            logging.info("HTTP metrics server stopped")