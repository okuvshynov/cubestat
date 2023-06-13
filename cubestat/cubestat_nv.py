#!/usr/bin/env python3

import plistlib
import subprocess
import curses
import argparse
import collections
import itertools
from threading import Thread, Lock
from math import floor
import psutil
import time
from ui import Percentages, CPUMode, Color

parser = argparse.ArgumentParser("./cubestat.py")
parser.add_argument('--refresh_ms', '-i', type=int, default=500, help='Update frequency, milliseconds')
parser.add_argument('--buffer_size', type=int, default=500, help='How many datapoints to store. Having it larger than screen width is a good idea as terminal window can be resized')
parser.add_argument('--cpu', type=CPUMode, default=CPUMode.by_core, choices=list(CPUMode), help='CPU mode - showing all cores, only cumulative by cluster or both. Can be toggled by pressing c.')
parser.add_argument('--color', type=Color, default=Color.mixed, choices=list(Color))
parser.add_argument('--percentages', type=Percentages, default=Percentages.hidden, choices=list(Percentages), help='Show/hide numeric utilization percentage. Can be toggled by pressing p.')
parser.add_argument('--disk', action="store_true", help="show disk read/write. Can be toggled by pressing d.")
parser.add_argument('--network', action="store_true", help="show network io. Can be toggled by pressing n.")
parser.add_argument('--count', type=int, default=2**63)

args = parser.parse_args()

# settings
spacing_width = 1
filling = '.'
colorschemes = {
    Color.green: [-1, 150, 107, 22],
    Color.red: [-1, 224, 138, 52],
    Color.blue: [-1, 189, 103, 17],
}

class Horizon:
    def __init__(self, stdscr):
        stdscr.nodelay(False)
        stdscr.timeout(50)
        curses.curs_set(0)
        curses.start_color()
        curses.use_default_colors()

        self.cpu_color = Color.green if args.color == Color.mixed else args.color
        self.gpu_color = Color.red if args.color == Color.mixed else args.color
        self.ane_color = Color.red if args.color == Color.mixed else args.color
        self.io_color = Color.blue if args.color == Color.mixed else args.color
        self.cells = self._cells()
        self.stdscr = stdscr

        # all of the fields below are mutable and can be accessed from 2 threads
        self.lock = Lock()
        self.cubes = collections.defaultdict(lambda: collections.deque(maxlen=args.buffer_size))
        self.colormap = {}
        self.snapshots_observed = 0
        self.snapshots_rendered = 0
        self.percentage_mode = args.percentages
        self.cpu_cubes = []
        self.cpu_cluster_cubes = []
        self.cpumode = args.cpu
        self.show_disk = args.disk
        self.show_network = args.network
        self.settings_changes = False
        self.disk_read_last = 0
        self.disk_written_last = 0
        self.network_read_last = 0
        self.network_written_last = 0

    def _cells(self):
        chrs = [' ', '▁', '▂', '▃', '▄', '▅', '▆', '▇', '█']
        cells = {}
        colorpair = 1
        for name, colors in colorschemes.items():
            cells[name] = []
            for fg, bg in zip(colors[1:], colors[:-1]):
                curses.init_pair(colorpair, fg, bg)
                cells[name].extend((chr, colorpair) for chr in chrs)
                colorpair += 1
        return cells

    def process_snapshot(self):
        initcolormap = not self.colormap
        ram_used = psutil.virtual_memory().percent
        cpu_load = psutil.cpu_percent(percpu=True)
        disk_load = psutil.disk_io_counters()
        disk_read_kb = disk_load.read_bytes / 2 ** 10
        disk_written_kb = disk_load.write_bytes / 2 ** 10
        nw_load = psutil.net_io_counters()
        nw_read_kb = nw_load.bytes_recv / 2 ** 10
        nw_written_kb = nw_load.bytes_sent / 2 ** 10

        with self.lock:
            cluster_title = f'Total CPU util %'
            if not cluster_title in self.cubes:
                self.cubes[cluster_title] = collections.deque(maxlen=args.buffer_size)
                self.cpu_cluster_cubes.append(cluster_title)
                self.colormap[cluster_title] = self.cpu_color
            # is this correct?
            total_load = 0.0
            for i, v in enumerate(cpu_load):
                title = f'CPU {i} util %'
                self.cubes[title].append(v)
                if initcolormap:
                    self.cpu_cubes.append(title)
                    self.colormap[title] = self.cpu_color
                total_load += v
            self.cubes[cluster_title].append(total_load / len(cpu_load))

            self.cubes['RAM used %'].append(ram_used)
            if initcolormap:
                self.colormap['RAM used %'] = self.cpu_color

            if initcolormap:
                self.colormap['disk read KB/s'] = self.io_color
                self.colormap['disk write KB/s'] = self.io_color
                self.disk_read_last = disk_read_kb
                self.disk_written_last = disk_written_kb

            self.cubes['disk read KB/s'].append(disk_read_kb - self.disk_read_last)
            self.cubes['disk write KB/s'].append(disk_written_kb - self.disk_written_last)
            self.disk_read_last = disk_read_kb
            self.disk_written_last = disk_written_kb

            if initcolormap:
                self.colormap['network i KB/s'] = self.io_color
                self.colormap['network w KB/s'] = self.io_color
                self.network_read_last = nw_read_kb
                self.network_written_last = nw_written_kb

            self.cubes['network i KB/s'].append(nw_read_kb - self.network_read_last)
            self.cubes['network w KB/s'].append(nw_written_kb - self.network_written_last)
            self.network_read_last = nw_read_kb
            self.network_written_last = nw_written_kb

            self.snapshots_observed += 1


    def wl(self, r, c, s, color=0):
        if r < 0 or r >= self.rows or c < 0:
            return
        if c + len(s) >= self.cols:
            s = s[:self.cols - c]
        try:
            self.stdscr.addstr(r, c, s, color)
        except:
            pass

    def wr(self, r, c, s, color=0):
        c = self.cols - c - 1
        if r < 0 or r >= self.rows or c < 0:
            return
        if c < len(s):
            s = s[-c:]
        try:
            self.stdscr.addstr(r, c - len(s) + 1, s, color)
        except:
            pass

    #@profile
    def render(self):
        with self.lock:
            if self.snapshots_observed >= args.count:
                exit(0)
            if self.snapshots_observed == self.snapshots_rendered and not self.settings_changes:
                return
        self.stdscr.erase()
        self.rows, self.cols = self.stdscr.getmaxyx()
        spacing = ' ' * spacing_width

        filter_cpu = lambda it : self.cpumode == CPUMode.all or (self.cpumode == CPUMode.by_cluster and it[0] not in self.cpu_cubes) or (self.cpumode == CPUMode.by_core and it[0] not in self.cpu_cluster_cubes)
        filter_io = lambda it : (self.show_disk or 'disk' not in it[0]) and (self.show_network or 'network' not in it[0]) 
        with self.lock:
            cubes = filter(lambda it: all([filter_cpu(it), filter_io(it)]), self.cubes.items())
            
            for i, (title, series) in enumerate(cubes):
                cells = self.cells[self.colormap[title]]
                range = len(cells)

                # indent is used to highlight cores which belong to the same cluster (efficiency vs performance).
                indent = '  ' if self.cpumode == CPUMode.all and title in self.cpu_cubes else ''

                titlestr = f'{indent}╔{spacing}{title}'
                self.wl(i * 2, 0, titlestr)
                self.wl(i * 2 + 1, 0, f'{indent}╚')
                
                index = max(0, len(series) - (self.cols - 2 * spacing_width - 2 - len(indent)))
                data_slice = list(itertools.islice(series, index, None))

                B = 100.0
                strvalue = f'last:{data_slice[-1]:3.0f}%{spacing}╗' if self.percentage_mode == Percentages.last else f'{spacing}╗'
                if 'disk' in title or 'network' in title:
                    B = max(data_slice)
                    B = float(1 if B == 0 else 2 ** (int((B - 1)).bit_length()))
                    strvalue =  f'last:{data_slice[-1]:3.0f}|{int(B)}Kb/s{spacing}╗' if self.percentage_mode == Percentages.last else f'{spacing}╗'

                title_filling = filling * (self.cols - len(strvalue) - len(titlestr))
                self.wl(i * 2, len(titlestr), title_filling)

                self.wr(i * 2, 0, strvalue)
                self.wr(i * 2 + 1, 0, f'{spacing}╝')

                scaler = range / B
                
                col = self.cols - (len(data_slice) + spacing_width) - 2

                for v in data_slice:
                    col += 1
                    cell_index = floor(v * scaler)
                    if cell_index <= 0:
                        continue
                    if cell_index >= range:
                        cell_index = range - 1
                    chr, color_pair = cells[cell_index]
                    self.stdscr.addch(i * 2 + 1, col, chr, curses.color_pair(color_pair))
                self.snapshots_rendered += 1
        self.stdscr.refresh()

    def loop(self):
        def reader_loop():
            begin_ts = time.time()
            n = 0
            d = args.refresh_ms / 1000.0
            while True:
                n += 1
                expected_time = begin_ts + n * d
                time.sleep(expected_time - time.time())
                self.process_snapshot()

        reader_thread = Thread(target=reader_loop, daemon=True)
        reader_thread.start()

        while True:
            self.render()
            key = self.stdscr.getch()
            if key == ord('q') or key == ord('Q'):
                exit(0)
            if key == ord('p'):
                with self.lock:
                    self.percentage_mode = self.percentage_mode.next()
                    self.settings_changes = True
            if key == ord('c'):
                with self.lock:
                    self.cpumode = self.cpumode.next()
                    self.settings_changes = True
            if key == ord('d'):
                with self.lock:
                    self.show_disk = not self.show_disk
                    self.settings_changes = True
            if key == ord('n'):
                with self.lock:
                    self.show_network = not self.show_network
                    self.settings_changes = True

def start(stdscr):
    h = Horizon(stdscr)
    h.loop()

def main():
    curses.wrapper(start)

if __name__ == '__main__':
    main()
