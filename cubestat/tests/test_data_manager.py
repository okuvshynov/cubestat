from cubestat.data import DataManager

import unittest
import collections


class TestDataManager(unittest.TestCase):
    def test_init(self):
        buffer_size = 10
        dm = DataManager(buffer_size)
        self.assertIsInstance(dm.data, collections.defaultdict)
        self.assertEqual(len(dm.data), 0)

    def test_update(self):
        buffer_size = 10
        dm = DataManager(buffer_size)
        updates = [("group1", "title1", 1), ("group1", "title2", 2), ("group2", "title3", 3)]
        dm.update(updates)
        self.assertEqual(len(dm.data), 2)
        self.assertEqual(len(dm.data["group1"]), 2)
        self.assertEqual(len(dm.data["group1"]["title1"]), 1)
        self.assertEqual(len(dm.data["group1"]["title2"]), 1)
        self.assertEqual(len(dm.data["group2"]), 1)
        self.assertEqual(len(dm.data["group2"]["title3"]), 1)

    def test_get_slice(self):
        buffer_size = 10
        dm = DataManager(buffer_size)
        series = collections.deque([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], maxlen=buffer_size)
        indent = "  "
        h_shift = 2
        cols = 20
        spacing = " "
        expected_slice = [1, 2, 3, 4, 5, 6, 7, 8]
        self.assertEqual(dm.get_slice(series, indent, h_shift, cols, spacing), expected_slice)

    def test_get_slice_shift(self):
        buffer_size = 10
        dm = DataManager(buffer_size)
        series = collections.deque([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], maxlen=buffer_size)
        indent = "  "
        h_shift = 2
        cols = 10
        spacing = " "
        expected_slice = [5, 6, 7, 8]
        self.assertEqual(dm.get_slice(series, indent, h_shift, cols, spacing), expected_slice)

    def test_data_gen(self):
        buffer_size = 10
        dm = DataManager(buffer_size)
        updates = [("group1", "title1", 1), ("group1", "title2", 2), ("group2", "title3", 3)]
        dm.update(updates)
        expected_data = [
            ("group1", "title1", collections.deque([1], maxlen=buffer_size)),
            ("group1", "title2", collections.deque([2], maxlen=buffer_size)),
            ("group2", "title3", collections.deque([3], maxlen=buffer_size)),
        ]
        self.assertEqual(list(dm.data_gen()), expected_data)


if __name__ == "__main__":
    unittest.main()
