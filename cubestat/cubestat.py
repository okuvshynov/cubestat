#!/usr/bin/env python3

import argparse
import collections
import curses
import itertools
import sys

from enum import Enum
from math import floor
from threading import Thread, Lock

from cubestat.readers.linux_reader import LinuxReader
from cubestat.readers.macos_reader import AppleReader

class EnumLoop(Enum):
    def next(self):
        values = list(self.__class__)
        return values[(values.index(self) + 1) % len(values)]
    
class EnumStr(Enum):
    def __str__(self):
        return self.value

class Percentages(EnumLoop, EnumStr):
    hidden = 'hidden'
    last = 'last'
    
class CPUMode(EnumLoop, EnumStr):
    all = 'all'
    by_cluster = 'by_cluster'
    by_core = 'by_core'
    
class Color(EnumStr):
    red = 'red'
    green = 'green'
    blue = 'blue'
    pink = 'pink'
    mixed = 'mixed'

parser = argparse.ArgumentParser("cubestat")
parser.add_argument('--refresh_ms', '-i', type=int, default=1000, help='Update frequency, milliseconds')
parser.add_argument('--buffer_size', type=int, default=500, help='How many datapoints to store. Having it larger than screen width is a good idea as terminal window can be resized')
parser.add_argument('--cpu', type=CPUMode, default=CPUMode.all, choices=list(CPUMode), help='CPU mode - showing all cores, only cumulative by cluster or both. Can be toggled by pressing c.')
parser.add_argument('--color', type=Color, default=Color.mixed, choices=list(Color))
parser.add_argument('--percentages', type=Percentages, default=Percentages.last, choices=list(Percentages), help='Show/hide numeric utilization percentage. Can be toggled by pressing p.')
parser.add_argument('--disk', action="store_true", default=True, help="Show disk read/write. Can be toggled by pressing d.")
parser.add_argument('--swap', action="store_true", default=True, help="Show swap . Can be toggled by pressing s.")
parser.add_argument('--network', action="store_true", default=True, help="Show network io. Can be toggled by pressing n.")
parser.add_argument('--no-disk', action="store_false", dest="disk", help="Hide disk read/write. Can be toggled by pressing d.")
parser.add_argument('--no-swap', action="store_false", default=True, help="Hide swap. Can be toggled by pressing s.")
parser.add_argument('--no-network', action="store_false", dest="network", help="Hide network io. Can be toggled by pressing n.")

args = parser.parse_args()

class Horizon:
    def __init__(self, stdscr, reader):
        stdscr.nodelay(False)
        stdscr.timeout(50)
        curses.curs_set(0)
        curses.start_color()
        curses.use_default_colors()

        self.spacing_width = 1
        self.filling = '.'

        self.cells = self.prepare_cells()
        self.stdscr = stdscr

        # all of the fields below are mutable and can be accessed from 2 threads
        self.lock = Lock()
        self.data = {k: collections.defaultdict(lambda: collections.deque(maxlen=args.buffer_size)) for k in ['cpu', 'ram', 'swap', 'accelerators',  'disk', 'network']}
        self.colormap = {
            'cpu': Color.green if args.color == Color.mixed else args.color,
            'ram': Color.pink if args.color == Color.mixed else args.color,
            'accelerators': Color.red if args.color == Color.mixed else args.color,
            'disk': Color.blue if args.color == Color.mixed else args.color,
            'network': Color.blue if args.color == Color.mixed else args.color,
            'swap': Color.pink if args.color == Color.mixed else args.color,
        }
        self.snapshots_observed = 0
        self.snapshots_rendered = 0
        self.percentage_mode = args.percentages
        self.cpumode = args.cpu
        self.show_disk = args.disk
        self.show_swap = args.swap
        self.show_network = args.network
        self.settings_changed = False
        self.reader = reader
        self.vertical_shift = 0
        self.horizontal_shift = 0

    def prepare_cells(self):
        chrs = [' ', '▁', '▂', '▃', '▄', '▅', '▆', '▇', '█']
        colorschemes = {
            Color.green: [-1, 150, 107, 22],
            Color.red: [-1, 224, 181, 138],
            Color.blue: [-1, 189, 146, 103],
            Color.pink: [-1, 223, 180, 137],
        }
        cells = {}
        colorpair = 1
        for name, colors in colorschemes.items():
            cells[name] = []
            for fg, bg in zip(colors[1:], colors[:-1]):
                curses.init_pair(colorpair, fg, bg)
                cells[name].extend((chr, colorpair) for chr in chrs)
                colorpair += 1
        return cells

    def process_snapshot(self, data, cpu_clusters):
        for group, vals in data:
            for title, value in vals.items():
                with self.lock:
                    self.data[group][title].append(value)

        with self.lock:
            self.cpu_clusters = cpu_clusters
            self.snapshots_observed += 1
            if self.horizontal_shift > 0:
                self.horizontal_shift += 1

    def write_string(self, row, col, s, color=0):
        if row < 0 or row >= self.rows or col < 0:
            return
        if col + len(s) > self.cols:
            s = s[:self.cols - col]
        try:
            self.stdscr.addstr(row, col, s, color)
        except:
            # TODO: log something
            pass

    def write_char(self, row, col, chr, color=0):
        if row < 0 or row >= self.rows or col < 0 or col >= self.cols:
            return
        try:
            self.stdscr.addch(row, col, chr, color)
        except:
            # TODO: log something
            pass

    # buckets is a list of factor/label, e.g. [(1024*1024, 'Mb'), (1024, 'Kb'), (1, 'b')]
    def format_measurement(self, spacing, curr, mx, buckets):
        if self.percentage_mode != Percentages.last:
            return f'{spacing}╗'
        for lim, unit in buckets[:-1]:
            if mx > lim:
                return f'last:{curr / lim :3.0f}|{int(mx / lim)}{unit}{spacing}╗'
        return f'last:{curr :3.0f}|{int(mx)}{buckets[-1][1]}{spacing}╗'

    def render(self):
        with self.lock:
            if self.snapshots_observed == self.snapshots_rendered and not self.settings_changed:
                return
        self.stdscr.erase()
        self.rows, self.cols = self.stdscr.getmaxyx()
        spacing = ' ' * self.spacing_width

        # Each chart takes two lines, with format roughly
        # ╔ GPU util %........................................................................last:  4% ╗
        # ╚ ▁▁▁  ▁    ▁▆▅▄ ▁▁▁      ▂ ▇▃▃▂█▃▇▁▃▂▁▁▂▁▁▃▃▂▁▂▄▄▁▂▆▁▃▁▂▃▁▁▁▂▂▂▂▂▂▁▁▃▂▂▁▂▁▃▄▃ ▁▁▃▁▄▂▃▂▂▂▃▃▅▅ ╝

        with self.lock:
            i = 0
            skip = self.vertical_shift
            for group_name, group in self.data.items():
                if group_name == 'disk' and not self.show_disk:
                    continue
                if group_name == 'network' and not self.show_network:
                    continue
                if group_name == 'swap' and not self.show_swap:
                    continue

                cells = self.cells[self.colormap[group_name]]
                range = len(cells)
                for title, series in group.items():
                    indent = ''

                    if group_name == 'cpu':
                        if self.cpumode == CPUMode.by_cluster and title not in self.cpu_clusters:
                            continue
                        if self.cpumode == CPUMode.by_core and title in self.cpu_clusters:
                            continue
                        if self.cpumode == CPUMode.all and title not in self.cpu_clusters:
                            indent = '  '
                    if skip > 0:
                        skip -= 1
                        continue

                    # render title and left border, for example
                    #
                    # ╔ GPU util %
                    # ╚
                    titlestr = f'{indent}╔{spacing}{title}'
                    self.write_string(i * 2, 0, titlestr)
                    self.write_string(i * 2 + 1, 0, f'{indent}╚')

                    # data slice size
                    length = len(series) - self.horizontal_shift if self.horizontal_shift > 0 else len(series)
                    
                    # chart area width
                    width = self.cols - 2 * self.spacing_width - 2 - len(indent)
                    index = max(0, length - width)
                    data_slice = list(itertools.islice(series, index, min(index + width, length)))

                    # for percentage-like measurements
                    B = 100.0
                    strvalue = f'last:{data_slice[-1]:3.0f}%{spacing}╗' if self.percentage_mode == Percentages.last else f'{spacing}╗'
                    
                    if group_name == 'disk' or group_name == 'network':
                        B = max(data_slice)
                        B = float(1 if B == 0 else 2 ** (int((B - 1)).bit_length()))
                        strvalue = self.format_measurement(spacing, data_slice[-1], B, [(1024 * 1024, 'Mb/s'), (1024, 'Kb/s'), (1, 'bytes/s')])

                    if group_name == 'swap':
                        B = max(data_slice)
                        B = float(1 if B == 0 else 2 ** (int((B - 1)).bit_length()))
                        strvalue = self.format_measurement(spacing, data_slice[-1], B, [(1024 * 1024, 'Mb'), (1024, 'Kb'), (1, 'bytes')])

                    # render the rest of title row
                    #
                    # ╔ GPU util %........................................................................last:  4% ╗
                    # ╚
                    title_filling = self.filling * (self.cols - len(strvalue) - len(titlestr))
                    self.write_string(i * 2, len(titlestr), title_filling)
                    self.write_string(i * 2, self.cols - len(strvalue), strvalue)

                    # render the right border
                    #
                    # ╔ GPU util %........................................................................last:  4% ╗
                    # ╚                                                                                             ╝
                    border = f'{spacing}╝'
                    self.write_string(i * 2 + 1, self.cols - len(border), border)

                    # Render the chart itself
                    #
                    # ╔ GPU util %........................................................................last:  4% ╗
                    # ╚ ▁▁▁  ▁    ▁▆▅▄ ▁▁▁      ▂ ▇▃▃▂█▃▇▁▃▂▁▁▂▁▁▃▃▂▁▂▄▄▁▂▆▁▃▁▂▃▁▁▁▂▂▂▂▂▂▁▁▃▂▂▁▂▁▃▄▃ ▁▁▃▁▄▂▃▂▂▂▃▃▅▅ ╝
                    scaler = range / B
                    col = self.cols - (len(data_slice) + self.spacing_width) - 2
                    for v in data_slice:
                        col += 1
                        cell_index = floor(v * scaler)
                        if cell_index <= 0:
                            continue
                        if cell_index >= range:
                            cell_index = range - 1
                        chr, color_pair = cells[cell_index]
                        self.write_char(i * 2 + 1, col, chr, curses.color_pair(color_pair))

                    i += 1

                self.snapshots_rendered += 1
                
        self.stdscr.refresh()

    def render_loop(self):
        self.stdscr.keypad(True)
        while True:
            self.render()
            key = self.stdscr.getch()
            if key == ord('q') or key == ord('Q'):
                exit(0)
            if key == ord('p'):
                with self.lock:
                    self.percentage_mode = self.percentage_mode.next()
                    self.settings_changed = True
            if key == ord('c'):
                with self.lock:
                    self.cpumode = self.cpumode.next()
                    self.settings_changed = True
            if key == ord('s'):
                with self.lock:
                    self.show_swap = not self.show_swap
                    self.settings_changed = True
            if key == ord('d'):
                with self.lock:
                    self.show_disk = not self.show_disk
                    self.settings_changed = True
            if key == ord('n'):
                with self.lock:
                    self.show_network = not self.show_network
                    self.settings_changed = True
            if key == curses.KEY_UP:
                with self.lock:
                    if self.vertical_shift > 0:
                        self.vertical_shift -= 1
                        self.settings_changed = True
            if key == curses.KEY_DOWN:
                with self.lock:
                    self.vertical_shift += 1
                    self.settings_changed = True
            if key == curses.KEY_LEFT:
                with self.lock:
                    if self.horizontal_shift + 1 < self.snapshots_observed:
                        self.horizontal_shift += 1
                        self.settings_changed = True
            if key == curses.KEY_RIGHT:
                with self.lock:
                    if self.horizontal_shift > 0:
                        self.horizontal_shift -= 1
                        self.settings_changed = True
            if key == ord('0'):
                with self.lock:
                    if self.horizontal_shift > 0:
                        self.horizontal_shift = 0
                        self.settings_changed = True

    def loop(self):
        reader_thread = Thread(target=self.reader.loop, daemon=True, args=[self.process_snapshot])
        reader_thread.start()
        self.render_loop()

def start(stdscr, reader):
    h = Horizon(stdscr, reader)
    h.loop()

def main():
    if sys.platform == "darwin":
        curses.wrapper(start, AppleReader(args.refresh_ms))
    if sys.platform == "linux" or sys.platform == "linux2":
        curses.wrapper(start, LinuxReader(args.refresh_ms))
    # TODO: write something about platform not supported

if __name__ == '__main__':
    main()
