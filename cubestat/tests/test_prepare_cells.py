from cubestat.colors import prepare_cells

from unittest.mock import patch
import unittest


class TestPrepareCells(unittest.TestCase):
    @patch('curses.init_pair')
    def test_prepare_cells(self, mock_init_pair):
        cells = prepare_cells()
        self.assertEqual(len(cells['green']), 27)
        self.assertEqual(mock_init_pair.call_count, 18)


if __name__ == '__main__':
    unittest.main()
