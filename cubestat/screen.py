import curses
from math import floor

from cubestat.colors import Colorschemes


class Screen:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.stdscr.nodelay(False)
        self.stdscr.timeout(50)
        curses.curs_set(0)
        curses.start_color()
        curses.use_default_colors()
        self.spacing = ' '
        self.colors = Colorschemes()

    def write_string(self, row, col, s, color=0):
        if col + len(s) > self.cols:
            s = s[:self.cols - col]
        try:
            self.stdscr.addstr(row, col, s, color)
        except curses.error:
            pass

    def write_char(self, row, col, chr, color=0):
        try:
            self.stdscr.addch(row, col, chr, color)
        except curses.error:
            pass

    def render_start(self):
        self.stdscr.erase()
        self.rows, self.cols = self.stdscr.getmaxyx()

    def render_done(self):
        self.stdscr.refresh()

    def ruler(self, ruler, items):
        for idx, value in items:
            ruler = self.inject_to_string(ruler, idx, value)
        return ruler

    def render_ruler(self, indent, title, base_ruler, items, row):
        ruler = self.ruler(base_ruler, items)
        title_str = f'{indent}╔{self.spacing}{title}'
        topright_border = f"{self.spacing}╗"
        title_filling = ruler[len(title_str):-len(topright_border)]
        bottomright_border = f'{self.spacing}╝'
        self.write_string(row, 0, title_str)
        self.write_string(row, len(title_str), title_filling)
        self.write_string(row, self.cols - len(topright_border), topright_border)
        self.write_string(row + 1, 0, f'{indent}╚')
        self.write_string(row + 1, self.cols - len(bottomright_border), bottomright_border)

    def render_chart(self, theme, max_value, data, row):
        cells = self.colors.get_cells(theme)
        scaler = len(cells) / max_value
        col_start = self.cols - (len(data) + len(self.spacing)) - 1

        for col, v in enumerate(data, start=col_start):
            cell_index = min(floor(v * scaler), len(cells) - 1)
            if cell_index <= 0:
                continue
            char, color_pair = cells[cell_index]
            self.write_char(row + 1, col, char, curses.color_pair(color_pair))

    def render_time(self, base_ruler, ruler_times, row):
        ruler = self.ruler(base_ruler, ruler_times)
        border_size = 1 + len(self.spacing)
        if len(ruler) > 2 * border_size:
            ruler = ruler[border_size: -border_size]
            self.write_string(row, 0, f"╚{self.spacing}{ruler}{self.spacing}╝")

    def inject_to_string(self, string, at, val):
        pos = self.cols - 1 - len(self.spacing) - 1 - at
        if pos > len(val):
            return string[:pos - len(val)] + val + "|" + string[pos + 1:]
        return string

    def chart_width(self, indent):
        return self.cols - 2 * len(self.spacing) - len(indent) - 2
