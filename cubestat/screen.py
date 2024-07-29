import curses

class Screen:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.stdscr.nodelay(False)
        self.stdscr.timeout(50)
        curses.curs_set(0)
        curses.start_color()
        curses.use_default_colors()

    def write_string(self, row, col, s, color=0):
        if col + len(s) > self.cols:
            s = s[:self.cols - col]
        try:
            self.stdscr.addstr(row, col, s, color)
        except:
            pass

    def write_char(self, row, col, chr, color=0):
        try:
            self.stdscr.addch(row, col, chr, color)
        except:
            pass

    def render_start(self):
        self.stdscr.erase()
        self.rows, self.cols = self.stdscr.getmaxyx()

    def render_done(self):
        self.stdscr.refresh()
