from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Sequence, Tuple, Type, TypeVar, Union
from argparse import ArgumentParser

from cubestat.common import SimpleMode


T = TypeVar('T', bound='base_metric')

# TODO: make this one metric_set or metric_group.
# each individual metric would be able to pick the implementation
# for formatting, etc.
class base_metric(ABC):
    mode: SimpleMode

    ###########################################################################
    # abstract methods each metric needs to implement
    ###########################################################################
    @abstractmethod
    def read(self, context: Dict[str, Any]) -> List[Tuple[str, str, float]]:
        """Read metric data from the system.
        
        Args:
            context: A dictionary containing context information for the metric
            
        Returns:
            List of (group, title, value) tuples representing the metrics
        """
        pass

    @abstractmethod
    def pre(self, title: str) -> Tuple[float, float]:
        """Prepare the metric for display.
        
        Args:
            title: The title of the metric
            
        Returns:
            A tuple containing min and max values for scaling
        """
        pass

    @abstractmethod
    def format(self, title: str, values: Sequence[float], idxs: Sequence[int]) -> Tuple[float, List[str]]:
        """Format metric values for display.
        
        Args:
            title: The title of the metric
            values: The metric values
            idxs: Indices to format
            
        Returns:
            A tuple containing the maximum value and formatted strings
        """
        pass

    @classmethod
    @abstractmethod
    def key(cls) -> str:
        """Return the key that identifies this metric."""
        pass

    ###########################################################################
    # methods with default implementation which each metric might override
    ###########################################################################

    # configure metric instance
    def configure(self, config: Dict[str, Any]) -> T:
        """Configure the metric instance.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            The configured metric instance
        """
        self.mode = SimpleMode.show
        return self

    # hotkey circle through the display modes
    def hotkey(self) -> Optional[str]:
        """Return the hotkey used to toggle this metric's display mode."""
        return None

    # if we define any options to select/toggle view mode
    @classmethod
    def configure_argparse(cls, parser: ArgumentParser) -> None:
        """Configure command line arguments for this metric.
        
        Args:
            parser: The argument parser to configure
        """
        pass

    # help message to be used for this metric.
    @classmethod
    def help(cls) -> Optional[str]:
        """Return help text for this metric."""
        return None
