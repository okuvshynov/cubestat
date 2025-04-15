import collections
import itertools
from typing import Any, Callable, DefaultDict, Deque, Dict, Iterator, List, Tuple, TypeVar

T = TypeVar('T')


class DataManager:
    """Manages time series data for metrics."""
    
    def __init__(self, buffer_size: int) -> None:
        """Initialize the data manager.
        
        Args:
            buffer_size: Maximum number of data points to keep per series
        """
        def init_series() -> Deque[float]:
            return collections.deque(maxlen=buffer_size)

        def init_group() -> DefaultDict[str, Deque[float]]:
            return collections.defaultdict(init_series)

        self.data: DefaultDict[str, DefaultDict[str, Deque[float]]] = collections.defaultdict(init_group)

    # Returns a slice of data row which will be visible on the screen
    def get_slice(self, series: Deque[T], h_shift: int, chart_width: int) -> List[T]:
        """Get a slice of data that will be visible on screen.
        
        Args:
            series: The time series data
            h_shift: Horizontal shift (scrolling)
            chart_width: Width of the chart in columns
            
        Returns:
            List of values to display
        """
        data_length = len(series) - h_shift if h_shift > 0 else len(series)
        index = max(0, data_length - chart_width)
        return list(itertools.islice(series, index, min(index + chart_width, data_length)))

    def update(self, updates: List[Tuple[str, str, float]]) -> None:
        """Update data with new values.
        
        Args:
            updates: List of (group, title, value) tuples
        """
        for (group, title, value) in updates:
            self.data[group][title].append(value)

    def data_gen(self) -> Iterator[Tuple[str, str, Deque[float]]]:
        """Generate all stored data series.
        
        Returns:
            Iterator yielding (group_name, title, series) tuples
        """
        for group_name, group in self.data.items():
            for title, series in group.items():
                yield (group_name, title, series)
