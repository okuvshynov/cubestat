"""CSV exporter for cubestat metrics."""

import csv
import sys
import time

from cubestat.metrics_registry import get_metrics
from cubestat.transformers import CSVTransformer


class CSVExporter:
    """CSV exporter that outputs metrics in standardized format."""

    def __init__(self, args):
        self.csv_transformer = CSVTransformer()
        self.metrics = get_metrics(args)
        self.writer = csv.writer(sys.stdout)
        self.header_written = False

        # Replace the transformer in each metric adapter to use CSV transformer
        for metric in self.metrics.values():
            if hasattr(metric, "transformer"):
                metric.transformer = self.csv_transformer

    def do_read(self, context) -> None:
        """CSV version of do_read - outputs standardized metric names."""
        # Collect all standardized metrics
        all_metrics = {}
        for group, metric in self.metrics.items():
            # Get raw data from collector
            raw_data = metric.collector.collect(context)
            # Transform with CSV transformer (preserves standardized names)
            csv_data = self.csv_transformer.transform(raw_data)
            # Add to combined metrics
            for metric_name, value in csv_data.items():
                all_metrics[metric_name] = value

        # Write CSV header on first output
        if not self.header_written:
            self.writer.writerow(["timestamp", "metric", "value"])
            self.header_written = True

        # Write data with timestamp
        timestamp = time.time()
        for metric_name, value in sorted(all_metrics.items()):
            self.writer.writerow([timestamp, metric_name, value])

        # Flush to ensure immediate output
        sys.stdout.flush()


def csv_export(platform, args):
    """Export metrics in CSV format without TUI initialization."""
    exporter = CSVExporter(args)

    # Use the same platform loop as TUI but with CSV output
    platform.loop(exporter.do_read)