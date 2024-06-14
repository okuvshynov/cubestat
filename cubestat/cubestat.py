#!/usr/bin/env python3

import argparse
import collections
import curses
import itertools
import logging
import os
import sys
import math

from math import floor
from threading import Thread, Lock

from cubestat.readers.linux_reader import LinuxReader
from cubestat.readers.macos_reader import AppleReader

from cubestat.common import EnumLoop, EnumStr
from cubestat.colors import Color, dark_colormap, light_colormap, colors_ansi256
from cubestat.timeline import plot_timeline

# TODO: joint with timeline mode?
class Legend(EnumLoop, EnumStr):
    hidden = 'off'
    last = 'last'
    
class CPUMode(EnumLoop, EnumStr):
    all = 'all'
    by_cluster = 'by_cluster'
    by_core = 'by_core'

class PowerMode(EnumLoop, EnumStr):
    combined = 'combined'
    all = 'all'
    off = 'off'

class GPUMode(EnumLoop, EnumStr):
    collapsed = 'collapsed'
    load_only = 'load_only'
    load_and_vram = 'load_and_vram'

class TimelineMode(EnumLoop, EnumStr):
    none = "none"
    one  = "one"
    mult = "mult"

class SimpleMode(EnumLoop, EnumStr):
    show = 'show'
    hide = 'hide'

def auto_cpu_mode() -> CPUMode:
     return CPUMode.all if os.cpu_count() < 40 else CPUMode.by_cluster

parser = argparse.ArgumentParser("cubestat")
parser.add_argument('--refresh_ms', '-i', type=int, default=1000, help='Update frequency, milliseconds')
parser.add_argument('--buffer_size', type=int, default=500, help='How many datapoints to store. Having it larger than screen width is a good idea as terminal window can be resized')
parser.add_argument('--cpu', type=CPUMode, default=auto_cpu_mode(), choices=list(CPUMode), help='CPU mode - showing all cores, only cumulative by cluster or both. Can be toggled by pressing c.')
parser.add_argument('--gpu', type=GPUMode, default=GPUMode.load_only, choices=list(GPUMode), help='GPU mode - hidden, showing all GPUs load, or showing load and vram usage. Can be toggled by pressing g.')
parser.add_argument('--power', type=PowerMode, default=PowerMode.combined, choices=list(PowerMode), help='Power mode - off, showing breakdown CPU/GPU/ANE load, or showing combined usage. Can be toggled by pressing p.')
parser.add_argument('--color', type=Color, default=Color.mixed, choices=list(Color))
parser.add_argument('--legend', type=Legend, default=Legend.last, choices=list(Legend), help='Show/hide numeric utilization percentage. Can be toggled by pressing l.')
parser.add_argument('--disk', type=SimpleMode, default=SimpleMode.show, choices=list(SimpleMode), help="Show disk read/write. Can be toggled by pressing d.")
parser.add_argument('--swap', type=SimpleMode, default=SimpleMode.show, choices=list(SimpleMode), help="Show swap . Can be toggled by pressing s.")
parser.add_argument('--network', type=SimpleMode, default=SimpleMode.show, choices=list(SimpleMode), help="Show network io. Can be toggled by pressing n.")

args = parser.parse_args()

class Horizon:
    def __init__(self, stdscr, reader):
        stdscr.nodelay(False)
        stdscr.timeout(50)
        curses.curs_set(0)
        curses.start_color()
        curses.use_default_colors()

        self.spacing = ' '
        self.filling = '.'
        self.timeline_interval = 20 # chars

        self.cells = self.prepare_cells()
        self.stdscr = stdscr

        self.lock = Lock()
        init_series = lambda: collections.deque(maxlen=args.buffer_size)
        init_group  = lambda: collections.defaultdict(init_series)
        self.data = collections.defaultdict(init_group)

        if args.color == Color.mixed:
            self.colormap = light_colormap
        elif args.color == Color.dark:
            self.colormap = dark_colormap
        else:
            self.colormap = {k: args.color for k, _ in light_colormap.items()}
        self.snapshots_observed = 0
        self.snapshots_rendered = 0
        self.settings_changed = False
        self.reader = reader
        self.vertical_shift = 0
        self.horizontal_shift = 0
        self.modes = {
            'time'  : TimelineMode.one,
            'legend': args.legend,
            'cpu'   : args.cpu,
            'gpu'   : args.gpu,
            'power' : args.power,
            'disk'  : args.disk,
            'swap'  : args.swap,
            'network'   : args.network,
        }

    def prepare_cells(self):
        chrs = [' ', '▁', '▂', '▃', '▄', '▅', '▆', '▇', '█']

        cells = {}
        colorpair = 1
        for name, colors in colors_ansi256.items():
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

    def label2(self, slice, buckets):
        mx = max(slice)
        mx = float(1 if mx == 0 else 2 ** (int((mx - 1)).bit_length()))
        return mx, self.format_measurement(self.spacing, slice[-1], mx, buckets)
    
    def label10(self, slice, buckets):
        mx = max(slice)
        mx = float(1 if mx <= 0 else 10 ** math.ceil(math.log10(mx)))
        return mx, self.format_measurement(self.spacing, slice[-1], mx, buckets)

    # buckets is a list of factor/label, e.g. [(1024*1024, 'Mb'), (1024, 'Kb'), (1, 'b')]
    def format_measurement(self, spacing, curr, mx, buckets):
        if self.modes['legend'] != Legend.last:
            return f'{spacing}╗'
        for lim, unit in buckets[:-1]:
            if mx > lim:
                return f'{curr / lim :3.0f}|{int(mx / lim)}{unit}{spacing}╗'
        return f'{curr :3.0f}|{int(mx)}{buckets[-1][1]}{spacing}╗'
    
    def format_legend(self, group_name, data_slice):
        # for percentage-like measurements
        B = 100.0
        strvalue = f'{data_slice[-1]:3.0f}%{self.spacing}╗' if self.modes['legend'] == Legend.last else f'{self.spacing}╗'
        
        if group_name == 'disk' or group_name == 'network':
            B, strvalue = self.label2(data_slice, [(1024 * 1024, 'MB/s'), (1024, 'KB/s'), (1, 'Bytes/s')])
            
        if group_name == 'swap':
            B, strvalue = self.label2(data_slice, [(1024 * 1024, 'MB'), (1024, 'KB'), (1, 'Bytes')])

        if group_name == 'power':
            B, strvalue = self.label10(data_slice, [(1000 * 1000, 'kW'), (1000, 'W'), (1, 'mW')])

        return B, strvalue
    
    def pre(self, group_name, title, is_multigpu):
        if group_name == 'disk' and self.modes['disk'] == SimpleMode.hide:
            return False, ''
        if group_name == 'network' and self.modes['network'] == SimpleMode.hide:
            return False, ''
        if group_name == 'swap' and self.modes['swap'] == SimpleMode.hide:
            return False, ''
        
        if group_name == 'cpu':
            if self.modes['cpu'] == CPUMode.by_cluster and title not in self.cpu_clusters:
                return False, ''
            if self.modes['cpu'] == CPUMode.by_core and title in self.cpu_clusters:
                return False, ''
            if self.modes['cpu'] == CPUMode.all and title not in self.cpu_clusters:
                return True, '  '

        if group_name == 'gpu':
            if is_multigpu and self.modes['gpu'] == GPUMode.collapsed and "Total GPU" not in title:
                return False, ''
            if self.modes['gpu'] == GPUMode.load_only and "vram" in title:
                return False, ''
            if is_multigpu and "Total GPU" not in title:
                return True, '  '

        if group_name == 'power':
            if self.modes['power'] == PowerMode.off:
                return False, ''
            if self.modes['power'] == PowerMode.combined and 'total' not in title:
                return False, ''
            if 'total' not in title:
                return True, '  '
        
        return True, ''
    
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

        row = 0
        with self.lock:
            if self.modes['time'] == TimelineMode.mult:
                for j in range(self.cols - 1 - self.timeline_interval, -1, -self.timeline_interval):
                    base_fill[j] = '|'
            base_line = "".join(base_fill)
            skip = self.vertical_shift
            is_multigpu = len(self.data['gpu']) > 1
            for group_name, group in self.data.items():
                for title, series in group.items():
                    show, indent = self.pre(group_name, title, is_multigpu)
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

                    # data slice size
                    length = len(series) - self.horizontal_shift if self.horizontal_shift > 0 else len(series)
                    
                    # chart area width
                    width = self.cols - 2 * len(self.spacing) - 2 - len(indent)
                    index = max(0, length - width)
                    data_slice = list(itertools.islice(series, index, min(index + width, length)))

                    max_value, value_str = self.format_legend(group_name, data_slice)

                    # render the rest of title row
                    #
                    # ╔ GPU util %............................................................................:  4% ╗
                    # ╚
                    title_filling = base_line[len(title_str):-len(value_str)]
                    self.write_string(row, len(title_str), title_filling)
                    self.write_string(row, self.cols - len(value_str), value_str)

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
                    cells = self.cells[self.colormap[group_name]]
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
            if self.modes['time'] != TimelineMode.none:
                tl = plot_timeline(self.cols - 2, args.refresh_ms, self.filling, self.timeline_interval, self.horizontal_shift)
                self.write_string(row, 0, "╚" + tl + "╝")             
        self.stdscr.refresh()

    def loop(self):
        reader_thread = Thread(target=self.reader.loop, daemon=True, args=[self.process_snapshot])
        reader_thread.start()
        self.stdscr.keypad(True)
        mode_keymap = {
            't': 'time',
            'c': 'cpu',
            'l': 'legend',
            'p': 'power',
            'g': 'gpu',
            'n': 'network',
            'd': 'disk',
            's': 'swap',
        }
        while True:
            self.render()
            key = self.stdscr.getch()
            if key == ord('q') or key == ord('Q'):
                exit(0)
            for k, mode in mode_keymap.items():
                if key == ord(k):
                    with self.lock:
                        self.modes[mode] = self.modes[mode].next()
                        self.settings_changed = True
                if key == ord(k.upper()):
                    with self.lock:
                        self.modes[mode] = self.modes[mode].prev()
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

def start(stdscr, reader):
    h = Horizon(stdscr, reader)
    h.loop()

def main():
    logging.basicConfig(filename='/tmp/cubestat.log', level=logging.INFO)
    if sys.platform == "darwin":
        curses.wrapper(start, AppleReader(args.refresh_ms))
    if sys.platform == "linux" or sys.platform == "linux2":
        curses.wrapper(start, LinuxReader(args.refresh_ms))
    logging.fatal(f'platform {sys.platform} is not supported yet.')

if __name__ == '__main__':
    main()
