from cubestat.common import format_measurement

import unittest


class TestFormatMeasurement(unittest.TestCase):

    def test_small_measurement(self):
        buckets = [(1024 ** 2, 'MB'), (1024, 'KB'), (1, 'Bytes')]
        curr = 15
        mx = 25
        self.assertEqual(format_measurement(curr, mx, buckets), ' 15 Bytes')

    def test_avg_measurement(self):
        buckets = [(1024 ** 2, 'MB'), (1024, 'KB'), (1, 'Bytes')]
        curr = 1500
        mx = 2050
        self.assertEqual(format_measurement(curr, mx, buckets), '  1 KB')


if __name__ == '__main__':
    unittest.main()
