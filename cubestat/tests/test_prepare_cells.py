from cubestat.colors import Colorschemes

from unittest.mock import patch
import unittest


class TestPrepareCells(unittest.TestCase):
    @patch('curses.init_pair')
    def test_prepare_cells(self, mock_init_pair):
        colors = Colorschemes()
        self.assertEqual(len(colors.schemes['green']), 25)
        self.assertEqual(mock_init_pair.call_count, 18)


if __name__ == '__main__':
    unittest.main()
