from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseCollector(ABC):
    """Base class for data collectors.
    
    Collectors are responsible for reading raw data from the system.
    They have no knowledge of formatting or presentation.
    """
    
    @abstractmethod
    def collect(self, context: Dict[str, Any]) -> Dict[str, float]:
        """Collect raw metric data.
        
        Args:
            context: Platform-specific context data
            
        Returns:
            Dictionary mapping metric names to values
        """
        pass
    
    @classmethod
    @abstractmethod
    def collector_id(cls) -> str:
        """Unique identifier for this collector."""
        pass
    
    def configure(self, config: Dict[str, Any]) -> 'BaseCollector':
        """Configure the collector instance."""
        return self