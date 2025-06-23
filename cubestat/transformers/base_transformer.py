"""Base transformer interface for metric transformation."""

from abc import ABC, abstractmethod
from typing import Dict, Any


class MetricTransformer(ABC):
    """Abstract base class for transforming metrics to output-specific formats."""
    
    @abstractmethod
    def transform(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform metrics from standardized format to output-specific format.
        
        Args:
            metrics: Dictionary of metrics in standardized dot-notation format
                    e.g., {"memory.system.total.used.percent": 75.5}
        
        Returns:
            Dictionary of transformed metrics suitable for the output format
        """
        pass
    
    @abstractmethod
    def should_include_metric(self, metric_name: str) -> bool:
        """
        Determine if a metric should be included in the output.
        
        Args:
            metric_name: Standardized metric name
            
        Returns:
            True if the metric should be included, False otherwise
        """
        pass