import math
from enum import Enum
from typing import Any, Dict, List, Sequence, Tuple, TypeVar, Union, Type

T = TypeVar('T', bound='DisplayMode')
Bucket = Tuple[float, str]


class DisplayMode(Enum):
    def __str__(self) -> str:
        return self.value

    def next(self: T) -> T:
        values = list(self.__class__)
        return values[(values.index(self) + 1) % len(values)]

    def prev(self: T) -> T:
        values = list(self.__class__)
        return values[(values.index(self) + len(values) - 1) % len(values)]


class SimpleMode(DisplayMode):
    show = 'show'
    hide = 'hide'


# buckets is a list of factor/label, e.g. [(1024*1024, 'Mb'), (1024, 'Kb'), (1, 'b')]
def format_measurement(curr: float, mx: float, buckets: List[Bucket]) -> str:
    """Format a measurement value using appropriate unit buckets.
    
    Args:
        curr: Current value to format
        mx: Maximum value (used to determine appropriate unit)
        buckets: List of (factor, unit) tuples for conversion
        
    Returns:
        Formatted measurement string
    """
    for lim, unit in buckets[:-1]:
        if mx > lim:
            return f'{curr / lim :3.0f} {unit}'
    return f'{curr :3.0f} {buckets[-1][1]}'


def label2(slice: Sequence[float], buckets: List[Bucket], idxs: Sequence[int]) -> Tuple[float, List[str]]:
    """Format measurements using power-of-2 scaling.
    
    Args:
        slice: The data slice to format
        buckets: Unit conversion buckets
        idxs: Indices to format
        
    Returns:
        Tuple of (max_value, formatted_values)
    """
    mx = max(slice) if slice else 0.0
    mx = float(1 if mx == 0 else 2 ** (int((mx - 1)).bit_length()))
    return mx, [format_measurement(slice[idx], mx, buckets) for idx in idxs]


def label10(slice: Sequence[float], buckets: List[Bucket], idxs: Sequence[int]) -> Tuple[float, List[str]]:
    """Format measurements using power-of-10 scaling.
    
    Args:
        slice: The data slice to format
        buckets: Unit conversion buckets
        idxs: Indices to format
        
    Returns:
        Tuple of (max_value, formatted_values)
    """
    mx = max(slice) if slice else 0.0
    mx = float(1 if mx <= 0 else 10 ** math.ceil(math.log10(mx)))
    return mx, [format_measurement(slice[idx], mx, buckets) for idx in idxs]


class RateReader:
    """Calculate rates from consecutive measurements."""
    
    def __init__(self, interval_ms: int) -> None:
        """Initialize a rate reader.
        
        Args:
            interval_ms: Interval between measurements in milliseconds
        """
        self.interval_s: float = interval_ms / 1000.0
        self.last: Dict[str, float] = {}

    def next(self, key: str, value: float) -> float:
        """Calculate rate of change for a value.
        
        Args:
            key: Identifier for the measurement
            value: Current measurement value
            
        Returns:
            Rate of change per second
        """
        if key not in self.last.keys():
            self.last[key] = value
            return 0.0
        res = (value - self.last[key]) / self.interval_s
        self.last[key] = value
        return res


def label_bytes(values: Sequence[float], idxs: Sequence[int]) -> Tuple[float, List[str]]:
    """Format values as byte measurements.
    
    Args:
        values: The values to format
        idxs: Indices to format
        
    Returns:
        Tuple of (max_value, formatted_values)
    """
    buckets: List[Bucket] = [
            (1024 ** 5, 'PB'),
            (1024 ** 4, 'TB'),
            (1024 ** 3, 'GB'),
            (1024 ** 2, 'MB'),
            (1024, 'KB'),
            (1, 'Bytes')
    ]
    return label2(values, buckets, idxs)


def label_bytes_per_sec(values: Sequence[float], idxs: Sequence[int]) -> Tuple[float, List[str]]:
    """Format values as bytes per second.
    
    Args:
        values: The values to format
        idxs: Indices to format
        
    Returns:
        Tuple of (max_value, formatted_values)
    """
    buckets: List[Bucket] = [
            (1024 ** 5, 'PB/s'),
            (1024 ** 4, 'TB/s'),
            (1024 ** 3, 'GB/s'),
            (1024 ** 2, 'MB/s'),
            (1024, 'KB/s'),
            (1, 'Bytes/s')
    ]
    return label2(values, buckets, idxs)
