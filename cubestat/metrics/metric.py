"""Unified metric implementation.

This module provides a single Metric class that replaces the complex inheritance
hierarchy of base_metric, MetricAdapter, and generic factory functions.
"""

from argparse import ArgumentParser
from typing import Any, Dict, List, Optional, Sequence, Tuple

from cubestat.collectors.base_collector import BaseCollector
from cubestat.presenters.base_presenter import BasePresenter
from cubestat.metrics_registry import presenter_registry


class Metric:
    """Unified metric implementation handling data flow between collector and presenter."""
    
    def __init__(self, 
                 key: str,
                 collector: BaseCollector, 
                 presenter: BasePresenter):
        """Initialize metric with collector and presenter.
        
        Args:
            key: The key identifying this metric (e.g., "cpu", "ram", "network")
            collector: Data collector for this metric
            presenter: Presenter for formatting and display
        """
        self.key = key
        self.collector = collector
        self.presenter = presenter
    
    def read(self, context: Dict[str, Any]) -> Dict[str, float]:
        """Read data using the collector and process through presenter.
        
        Args:
            context: Context information for data collection
            
        Returns:
            Dictionary of metric names to values
        """
        # Collector returns standardized metric names
        standardized_data = self.collector.collect(context)
        
        # Process directly through presenter (handles standardized names)
        return self.presenter.process_data(standardized_data)
    
    def pre(self, title: str) -> Tuple[bool, str]:
        """Prepare metric for display - delegate to presenter.
        
        Args:
            title: The metric title
            
        Returns:
            Tuple of (should_display, formatted_title)
        """
        return self.presenter.pre(title)
    
    def format(self, title: str, values: Sequence[float], idxs: Sequence[int]) -> Tuple[float, List[str]]:
        """Format metric values for display - delegate to presenter.
        
        Args:
            title: The metric title
            values: The metric values
            idxs: Indices to format
            
        Returns:
            Tuple of (max_value, formatted_strings)
        """
        return self.presenter.format(title, values, idxs)
    
    def hotkey(self) -> Optional[str]:
        """Get hotkey for this metric - delegate to presenter.
        
        Returns:
            Hotkey string or None
        """
        return self.presenter.hotkey()
    
    def configure_argparse(self, parser: ArgumentParser) -> None:
        """Configure command line arguments for this metric.
        
        Args:
            parser: The argument parser to configure
        """
        presenter_cls = presenter_registry.get(self.key)
        if presenter_cls:
            presenter_cls.configure_argparse(parser)
    
    @property
    def mode(self):
        """Get the current display mode from the presenter."""
        return self.presenter.mode
    
    @mode.setter  
    def mode(self, value):
        """Set the display mode on the presenter."""
        self.presenter.mode = value
    
    def configure(self, config: Dict[str, Any]) -> "Metric":
        """Configure both collector and presenter.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            The configured metric instance
        """
        self.collector.configure(config)
        self.presenter.configure(config)
        return self
    
    @classmethod
    def key(cls) -> str:
        """Return the key for this metric class.
        
        This is a compatibility method for the metrics registry.
        The actual key is stored as an instance attribute.
        """
        # This will be overridden in the factory-created classes
        raise NotImplementedError("key() must be implemented by subclasses")