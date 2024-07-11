#!/usr/bin/env python3

import argparse
import collections
import curses
import itertools
import logging
import sys

from math import floor
from threading import Thread, Lock

from cubestat.platforms.linux import LinuxPlatform
from cubestat.platforms.macos import MacOSPlatform

from cubestat.common import DisplayMode
from cubestat.colors import get_theme, prepare_cells, ColorTheme

from cubestat.metrics.registry import get_metrics, metrics_configure_argparse
from cubestat.metrics import cpu, gpu, memory, accel, swap, network, disk, power

class ViewMode(DisplayMode):
    off = "off"
    one = "one"
    all = "all"

class Horizon:
    def __init__(self, stdscr, platform, args):
        stdscr.nodelay(False)
        stdscr.timeout(50)
        curses.curs_set(0)
        curses.start_color()
        curses.use_default_colors()

        self.spacing = ' '
        self.filling = '.'
        self.timeline_interval = 20 # chars

        self.cells = prepare_cells()
        self.stdscr = stdscr

        self.lock = Lock()
        init_series = lambda: collections.deque(maxlen=args.buffer_size)
        init_group  = lambda: collections.defaultdict(init_series)
        self.data   = collections.defaultdict(init_group)

        self.snapshots_observed = 0
        self.snapshots_rendered = 0
        self.settings_changed = False
        self.platform = platform
        self.v_shift = 0
        self.h_shift = 0

        self.view = ViewMode.one
        self.theme = ColorTheme.col

        self.refresh_ms = args.refresh_ms
        self.metrics = get_metrics(args)

    def do_read(self, context):
        for group, metric in self.metrics.items():
            datapoint = metric.read(context)
            for title, value in datapoint.items():
                with self.lock:
                    self.data[group][title].append(value)

        with self.lock:
            self.snapshots_observed += 1
            if self.h_shift > 0:
                self.h_shift += 1

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
    
    def max_val(self, group_name, title, data_slice):
        max_value, _ = self.metrics[group_name].format(title, data_slice, [-1])
        return max_value
    
    def format_value(self, group_name, title, data_slice, idx):
        _, values = self.metrics[group_name].format(title, data_slice, [idx])
        return f'{values[0]}' if self.view != ViewMode.off else ''
    
    def get_col(self, ago):
        return self.cols - 1 - len(self.spacing) - 1 - ago
    
    def vertical_time(self, at, curr_line):
        str_pos = self.get_col(at)
        time_s = (self.refresh_ms * (at + self.h_shift)) / 1000.0
        time_str = f'-{time_s:.2f}s'
        if str_pos > len(time_str):
            curr_line = curr_line[:str_pos - len(time_str)] + time_str + "|" + curr_line[str_pos + 1:]
        return curr_line
    
    def vertical_val(self, group_name, title, at, data_slice, curr_line):
        if at >= len(data_slice):
            return curr_line
        data_index = - at - 1
        v = self.format_value(group_name, title, data_slice, data_index)
        str_pos = self.get_col(at)
        if str_pos > len(v):
            curr_line = curr_line[:str_pos - len(v)] + v + "|" + curr_line[str_pos + 1:]
        return curr_line

    def get_slice(self, series, indent):
        data_length = len(series) - self.h_shift if self.h_shift > 0 else len(series)
        chart_width = self.cols - 2 * len(self.spacing) - 2 - len(indent)
        index = max(0, data_length - chart_width)
        return list(itertools.islice(series, index, min(index + chart_width, data_length)))

    def render(self):
        with self.lock:
            if self.snapshots_rendered > self.snapshots_observed:
                logging.fatal('self.snapshots_rendered > self.snapshots_observed')
                exit(0)
            if self.snapshots_observed == self.snapshots_rendered and not self.settings_changed:
                return
        self.stdscr.erase()
        self.rows, self.cols = self.stdscr.getmaxyx()

        # Each chart takes two lines, with format roughly
        # ╔ GPU util %............................................................................:  4% ╗
        # ╚ ▁▁▁  ▁    ▁▆▅▄ ▁▁▁      ▂ ▇▃▃▂█▃▇▁▃▂▁▁▂▁▁▃▃▂▁▂▄▄▁▂▆▁▃▁▂▃▁▁▁▂▂▂▂▂▂▁▁▃▂▂▁▂▁▃▄▃ ▁▁▃▁▄▂▃▂▂▂▃▃▅▅ ╝

        base_fill = ['.'] * self.cols
        base_line = "".join(base_fill)

        row = 0
        with self.lock:
            if self.view != ViewMode.off:
                for ago in range(0, self.cols, self.timeline_interval):
                    base_fill[self.get_col(ago)] = '|'
                    if self.view != ViewMode.all:
                        break
            
            skip = self.v_shift
            for group_name, group in self.data.items():
                for title, series in group.items():
                    show, indent = self.metrics[group_name].pre(title)

                    if not show:
                        continue
                    
                    if skip > 0:
                        skip -= 1
                        continue

                    # render title and left border, for example
                    #
                    # ╔ GPU util %
                    # ╚
                    title_str = f'{indent}╔{self.spacing}{title}'
                    self.write_string(row, 0, title_str)
                    self.write_string(row + 1, 0, f'{indent}╚')

                    data_slice = self.get_slice(series, indent)
                    max_value = self.max_val(group_name, title, data_slice)

                    # render the rest of title row
                    #
                    # ╔ GPU util %............................................................................:  4% ╗
                    # ╚
                    
                    topright_border = f"{self.spacing}╗"
                    curr_line = base_line
                    if self.view != ViewMode.off:
                        for ago in range(0, self.cols, self.timeline_interval):
                            curr_line = self.vertical_val(group_name, title, ago, data_slice, curr_line)
                            if self.view != ViewMode.all:
                                break
                    title_filling = curr_line[len(title_str):-len(topright_border)]
                    self.write_string(row, len(title_str), title_filling)
                    self.write_string(row, self.cols - len(topright_border), topright_border)

                    # render the right border
                    #
                    # ╔ GPU util %............................................................................:  4% ╗
                    # ╚                                                                                             ╝
                    border = f'{self.spacing}╝'
                    self.write_string(row + 1, self.cols - len(border), border)

                    # Render the chart itself
                    #
                    # ╔ GPU util %............................................................................:  4% ╗
                    # ╚ ▁▁▁  ▁    ▁▆▅▄ ▁▁▁      ▂ ▇▃▃▂█▃▇▁▃▂▁▁▂▁▁▃▃▂▁▂▄▄▁▂▆▁▃▁▂▃▁▁▁▂▂▂▂▂▂▁▁▃▂▂▁▂▁▃▄▃ ▁▁▃▁▄▂▃▂▂▂▃▃▅▅ ╝
                    cells = self.cells[get_theme(group_name, self.theme)]
                    scaler = len(cells) / max_value
                    col = self.cols - (len(data_slice) + len(self.spacing)) - 2
                    for v in data_slice:
                        col += 1
                        cell_index = floor(v * scaler)
                        if cell_index <= 0:
                            continue
                        if cell_index >= len(cells):
                            cell_index = len(cells) - 1
                        chr, color_pair = cells[cell_index]
                        self.write_char(row + 1, col, chr, curses.color_pair(color_pair))

                    row += 2
            self.snapshots_rendered = self.snapshots_observed
            self.settings_changed   = False
            if self.view != ViewMode.off:
                curr_line = base_line
                for ago in range(0, self.cols, self.timeline_interval):
                    curr_line = self.vertical_time(ago, curr_line)
                curr_line = curr_line[len(self.spacing) + 1:  - len(self.spacing) - 1]

                self.write_string(row, 0, f"╚{self.spacing}{curr_line}{self.spacing}╝")

        self.stdscr.refresh()

    def loop(self):
        t = Thread(target=self.platform.loop, daemon=True, args=[self.do_read])
        t.start()
        self.stdscr.keypad(True)
        hotkeys = [(m.hotkey(), m) for m in self.metrics.values() if m.hotkey()]
        while True:
            self.render()
            key = self.stdscr.getch()
            if key == ord('q') or key == ord('Q'):
                exit(0)
            for k, metric in hotkeys:
                if key == ord(k):
                    with self.lock:
                        metric.mode = metric.mode.next()
                        self.settings_changed = True
                if key == ord(k.upper()):
                    with self.lock:
                        metric.mode = metric.mode.prev()
                        self.settings_changed = True
            if key == curses.KEY_UP:
                with self.lock:
                    if self.v_shift > 0:
                        self.v_shift -= 1
                        self.settings_changed = True
            if key == curses.KEY_DOWN:
                with self.lock:
                    self.v_shift += 1
                    self.settings_changed = True
            if key == curses.KEY_LEFT:
                with self.lock:
                    if self.h_shift + 1 < self.snapshots_observed:
                        self.h_shift += 1
                        self.settings_changed = True
            if key == curses.KEY_RIGHT:
                with self.lock:
                    if self.h_shift > 0:
                        self.h_shift -= 1
                        self.settings_changed = True
            if key == ord('0'):
                with self.lock:
                    if self.h_shift > 0:
                        self.h_shift = 0
                        self.settings_changed = True
            if key == ord('v'):
                with self.lock:
                    self.view = self.view.next()
                    self.settings_changed = True
            if key == ord('V'):
                with self.lock:
                    self.view = self.view.prev()
                    self.settings_changed = True
            if key == ord('t'):
                with self.lock:
                    self.theme = self.theme.next()
                    self.settings_changed = True
            if key == ord('T'):
                with self.lock:
                    self.theme = self.theme.prev()
                    self.settings_changed = True

def start(stdscr, platform, args):
    h = Horizon(stdscr, platform, args)
    h.loop()

def main():
    logging.basicConfig(filename='/tmp/cubestat.log', level=logging.INFO)
    parser = argparse.ArgumentParser("cubestat")
    parser.add_argument('--refresh_ms', '-i', type=int, default=1000, help='Update frequency, milliseconds')
    parser.add_argument('--buffer_size', type=int, default=500, help='How many datapoints to store. Having it larger than screen width is a good idea as terminal window can be resized')
    parser.add_argument('--view', type=ViewMode, default=ViewMode.one, choices=list(ViewMode), help='legend/values/time mode. Can be toggled by pressing v.')

    metrics_configure_argparse(parser)
    args = parser.parse_args()
    if sys.platform == "darwin":
        curses.wrapper(start, MacOSPlatform(args.refresh_ms), args)
    if sys.platform == "linux" or sys.platform == "linux2":
        curses.wrapper(start, LinuxPlatform(args.refresh_ms), args)
    logging.fatal(f'platform {sys.platform} is not supported yet.')

if __name__ == '__main__':
    main()
