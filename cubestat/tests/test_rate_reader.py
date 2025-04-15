"""Tests for the RateReader class."""

import unittest
from cubestat.common import RateReader


class TestRateReader(unittest.TestCase):
    """Test cases for the RateReader class."""

    def test_init(self) -> None:
        """Test initialization of RateReader."""
        interval_ms = 1000
        reader = RateReader(interval_ms)
        self.assertEqual(reader.interval_s, 1.0)
        self.assertEqual(reader.last, {})

    def test_next_first_call(self) -> None:
        """Test that first call to next returns 0."""
        interval_ms = 1000
        reader = RateReader(interval_ms)
        key = "test_key"
        value = 100.0
        rate = reader.next(key, value)
        
        self.assertEqual(rate, 0.0)
        self.assertEqual(reader.last[key], value)

    def test_next_positive_rate(self) -> None:
        """Test calculation of positive rate."""
        interval_ms = 1000
        reader = RateReader(interval_ms)
        key = "test_key"
        
        # First call initializes the value
        reader.next(key, 100.0)
        
        # Second call calculates the rate
        rate = reader.next(key, 200.0)
        
        # Rate should be (200 - 100) / 1.0 = 100.0 units per second
        self.assertEqual(rate, 100.0)
        self.assertEqual(reader.last[key], 200.0)

    def test_next_negative_rate(self) -> None:
        """Test calculation of negative rate."""
        interval_ms = 1000
        reader = RateReader(interval_ms)
        key = "test_key"
        
        # First call initializes the value
        reader.next(key, 200.0)
        
        # Second call calculates the rate
        rate = reader.next(key, 100.0)
        
        # Rate should be (100 - 200) / 1.0 = -100.0 units per second
        self.assertEqual(rate, -100.0)
        self.assertEqual(reader.last[key], 100.0)

    def test_next_multiple_keys(self) -> None:
        """Test that RateReader can handle multiple keys."""
        interval_ms = 1000
        reader = RateReader(interval_ms)
        
        # Initialize and update key1
        reader.next("key1", 100.0)
        rate1 = reader.next("key1", 150.0)
        
        # Initialize and update key2
        reader.next("key2", 200.0)
        rate2 = reader.next("key2", 250.0)
        
        self.assertEqual(rate1, 50.0)
        self.assertEqual(rate2, 50.0)
        self.assertEqual(reader.last["key1"], 150.0)
        self.assertEqual(reader.last["key2"], 250.0)

    def test_different_intervals(self) -> None:
        """Test that different intervals affect the calculated rate."""
        # 2 second interval
        reader1 = RateReader(2000)
        # 1 second interval
        reader2 = RateReader(1000)
        
        key = "test_key"
        
        # Initialize both readers
        reader1.next(key, 100.0)
        reader2.next(key, 100.0)
        
        # Update both readers with same value change
        rate1 = reader1.next(key, 200.0)
        rate2 = reader2.next(key, 200.0)
        
        # Rate1 should be (200 - 100) / 2.0 = 50.0 units per second
        # Rate2 should be (200 - 100) / 1.0 = 100.0 units per second
        self.assertEqual(rate1, 50.0)
        self.assertEqual(rate2, 100.0)


if __name__ == "__main__":
    unittest.main()