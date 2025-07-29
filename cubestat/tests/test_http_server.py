"""Tests for HTTP server functionality."""

import json
import time
import unittest
import urllib.error
import urllib.request

from cubestat.data import DataManager
from cubestat.http_server import HTTPMetricsServer


class TestHTTPServer(unittest.TestCase):
    """Test cases for HTTP metrics server."""

    def setUp(self):
        """Set up test environment."""
        self.data_manager = DataManager(buffer_size=100)
        self.host = "localhost"
        self.port = 0  # Let OS choose a free port
        self.server = None

    def tearDown(self):
        """Clean up after tests."""
        if self.server:
            self.server.stop()

    def test_server_starts_and_stops(self):
        """Test that HTTP server can start and stop cleanly."""
        self.server = HTTPMetricsServer(self.host, 8999, self.data_manager, 1000)
        
        # Server should start without errors
        self.server.start()
        time.sleep(0.1)  # Give server time to start
        
        # Server should stop without errors
        self.server.stop()

    def test_metrics_endpoint_empty_data(self):
        """Test /metrics endpoint with no data."""
        self.server = HTTPMetricsServer(self.host, 8998, self.data_manager, 1000)
        self.server.start()
        time.sleep(0.1)
        
        try:
            url = f"http://{self.host}:8998/metrics"
            with urllib.request.urlopen(url) as response:
                self.assertEqual(response.getcode(), 200)
                self.assertEqual(response.headers.get('Content-Type'), 'application/json')
                
                data = json.loads(response.read().decode('utf-8'))
                self.assertIn('metrics', data)
                self.assertEqual(data['metrics'], {})
                self.assertIn('metadata', data)
                self.assertEqual(data['metadata']['refresh_ms'], 1000)
        finally:
            self.server.stop()

    def test_metrics_endpoint_with_data(self):
        """Test /metrics endpoint with sample data."""
        # Add some test data to data manager
        test_updates = [
            ('cpu', 'core.0.utilization.percent', 25.5),
            ('memory', 'system.used.percent', 75.2),
            ('cpu', 'core.1.utilization.percent', 30.1),
        ]
        self.data_manager.update(test_updates)
        
        self.server = HTTPMetricsServer(self.host, 8997, self.data_manager, 1000)
        self.server.start()
        time.sleep(0.1)
        
        try:
            url = f"http://{self.host}:8997/metrics"
            with urllib.request.urlopen(url) as response:
                self.assertEqual(response.getcode(), 200)
                
                data = json.loads(response.read().decode('utf-8'))
                self.assertIn('metrics', data)
                
                # Check CPU group
                self.assertIn('cpu', data['metrics'])
                cpu_metrics = data['metrics']['cpu']
                self.assertIn('core.0.utilization.percent', cpu_metrics)
                self.assertIn('core.1.utilization.percent', cpu_metrics)
                
                # Check values
                self.assertEqual(cpu_metrics['core.0.utilization.percent']['current_value'], 25.5)
                self.assertEqual(cpu_metrics['core.1.utilization.percent']['current_value'], 30.1)
                
                # Check memory group
                self.assertIn('memory', data['metrics'])
                memory_metrics = data['metrics']['memory']
                self.assertIn('system.used.percent', memory_metrics)
                self.assertEqual(memory_metrics['system.used.percent']['current_value'], 75.2)
                
        finally:
            self.server.stop()

    def test_404_for_unknown_endpoint(self):
        """Test that unknown endpoints return 404."""
        self.server = HTTPMetricsServer(self.host, 8996, self.data_manager, 1000)
        self.server.start()
        time.sleep(0.1)
        
        try:
            url = f"http://{self.host}:8996/unknown"
            with self.assertRaises(urllib.error.HTTPError) as cm:
                urllib.request.urlopen(url)
            self.assertEqual(cm.exception.code, 404)
        finally:
            self.server.stop()

    def test_cors_headers(self):
        """Test that CORS headers are set correctly."""
        self.server = HTTPMetricsServer(self.host, 8995, self.data_manager, 1000)
        self.server.start()
        time.sleep(0.1)
        
        try:
            url = f"http://{self.host}:8995/metrics"
            with urllib.request.urlopen(url) as response:
                self.assertEqual(response.headers.get('Access-Control-Allow-Origin'), '*')
        finally:
            self.server.stop()

    def test_metadata_in_response(self):
        """Test that metadata with refresh_ms is included in response."""
        refresh_ms = 2500
        self.server = HTTPMetricsServer(self.host, 8994, self.data_manager, refresh_ms)
        self.server.start()
        time.sleep(0.1)
        
        try:
            url = f"http://{self.host}:8994/metrics"
            with urllib.request.urlopen(url) as response:
                data = json.loads(response.read().decode('utf-8'))
                
                # Check metadata exists
                self.assertIn('metadata', data)
                metadata = data['metadata']
                
                # Check refresh_ms in metadata
                self.assertIn('refresh_ms', metadata)
                self.assertEqual(metadata['refresh_ms'], refresh_ms)
                
        finally:
            self.server.stop()


if __name__ == '__main__':
    unittest.main()