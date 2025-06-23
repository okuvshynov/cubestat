"""TUI transformer - converts standardized names back to presenter-friendly format."""

from typing import Any, Dict

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

        # Memory metrics - migrated to MemoryPresenter.process_data()

        # Network metrics - migrated to NetworkPresenter.process_data()
        # Disk metrics - migrated to DiskPresenter.process_data()
        # Power metrics - migrated to PowerPresenter.process_data()

        # Swap metrics - migrated to SwapPresenter.process_data()
        # Accel metrics - migrated to AccelPresenter.process_data()
        # Mock metrics - migrated to MockPresenter.process_data()

        # GPU metrics - migrated to GPUPresenter.process_data()

        # CPU metrics - migrated to CPUPresenter.process_data()

        # Pass through metrics for presenters to handle directly
        for key, value in metrics.items():
            if key.startswith(("memory.", "network.", "disk.", "power.", "swap.", "accel.", "mock.", "gpu.", "cpu.")):
                transformed[key] = value

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
