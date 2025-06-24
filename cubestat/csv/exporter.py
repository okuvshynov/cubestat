"""CSV exporter for cubestat metrics."""

import csv
import sys
import time

from cubestat.metrics_registry import get_metrics


class CSVExporter:
    """CSV exporter that outputs metrics in standardized format."""

    def __init__(self, args):
        self.metrics = get_metrics(args)
        self.writer = csv.writer(sys.stdout)
        self.header_written = False

    def do_read(self, context) -> None:
        """CSV version of do_read - outputs standardized metric names."""
        # Collect all standardized metrics
        all_metrics = {}
        for group, metric in self.metrics.items():
            # Get standardized data directly from collector
            standardized_data = metric.collector.collect(context)
            # Add to combined metrics (no transformation needed for CSV)
            for metric_name, value in standardized_data.items():
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