from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Sequence, Tuple
from argparse import ArgumentParser

from cubestat.common import SimpleMode


class BasePresenter(ABC):
    """Base class for metric presenters.
    
    Presenters are responsible for formatting and displaying metric data.
    They define UI configuration but don't collect data.
    """
    
    mode: SimpleMode
    
    @abstractmethod
    def format(self, title: str, values: Sequence[float], idxs: Sequence[int]) -> Tuple[float, List[str]]:
        """Format metric values for display."""
        pass
    
    @abstractmethod
    def pre(self, title: str) -> Tuple[bool, str]:
        """Prepare the metric for display."""
        pass
    
    @classmethod
    @abstractmethod
    def key(cls) -> str:
        """Return the key that identifies this presenter."""
        pass
    
    
    def hotkey(self) -> Optional[str]:
        """Return the hotkey for toggling display mode."""
        return None
    
    @classmethod
    def configure_argparse(cls, parser: ArgumentParser) -> None:
        """Configure command line arguments."""
        pass
    
    def configure(self, config: Dict[str, Any]) -> 'BasePresenter':
        """Configure the presenter instance."""
        self.mode = SimpleMode.show
        return self
    
    @abstractmethod
    def process_data(self, raw_data: Dict[str, Any]) -> Dict[str, float]:
        """Convert collector data to display format with proper titles."""
        pass