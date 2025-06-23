"""CSV transformer - preserves standardized metric names for scripting."""

from typing import Dict, Any
from .base_transformer import MetricTransformer


class CSVTransformer(MetricTransformer):
    """Transformer for CSV output format."""
    
    def transform(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        For CSV, we preserve the standardized dot-notation format.
        
        Args:
            metrics: Dictionary of metrics in standardized format
        
        Returns:
            Same metrics unchanged (CSV benefits from hierarchical names)
        """
        return metrics
    
    def should_include_metric(self, metric_name: str) -> bool:
        """
        Include all metrics in CSV output.
        
        Args:
            metric_name: Standardized metric name
            
        Returns:
            Always True for CSV (include everything)
        """
        return True