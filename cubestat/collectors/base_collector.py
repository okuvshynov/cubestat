from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseCollector(ABC):
    """Base class for data collectors.
    
    Collectors are responsible for reading raw data from the system.
    They have no knowledge of formatting or presentation.
    """
    
    @abstractmethod
    def collect(self, context: Dict[str, Any]) -> Dict[str, float]:
        """Collect metric data.
        
        Args:
            context: Platform-specific context data
            
        Returns:
            Dictionary mapping metric names to values.
            New collectors should return standardized names (e.g., "memory.system.total.used.percent").
            Legacy collectors may return old names (e.g., "used_percent").
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