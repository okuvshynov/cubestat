#!/usr/bin/env python3

import plistlib
import subprocess
import curses
import argparse
import collections
import itertools
import logging
from threading import Thread, Lock
from enum import Enum

logging.basicConfig(filename='/tmp/cubestat.log')

class Percentages(Enum):
    hidden = 'hidden'
    last = 'last'

    def __str__(self):
        return self.value
    
    def other(self):
        return Percentages.hidden if self == Percentages.last else Percentages.last

class CPUMode(Enum):
    all = 'all'
    by_cluster = 'by_cluster'
    by_core = 'by_core'

    def __str__(self):
        return self.value
    
    def next(self):
        values = list(CPUMode)
        return values[(values.index(self) + 1) % len(values)]
    
class Color(Enum):
    red = 'red'
    green = 'green'
    blue = 'blue'
    mixed = 'mixed'

    def __str__(self):
        return self.value

parser = argparse.ArgumentParser("./cubestat.py")
parser.add_argument('--refresh_ms', '-i', type=int, default=500, help='This argument is passed to powermetrics as -i')
parser.add_argument('--buffer_size', type=int, default=500, help='How many datapoints to store. Having it larger than screen width is a good idea as terminal window can be resized')
parser.add_argument('--cpu', type=CPUMode, default=CPUMode.by_core, choices=list(CPUMode), help='CPU mode - showing all cores, only cumulative by cluster or both. Can be toggled by pressing c.')
parser.add_argument('--color', type=Color, default=Color.mixed, choices=list(Color))
parser.add_argument('--percentages', type=Percentages, default=Percentages.hidden, choices=list(Percentages), help='Show numeric utilization percentage. Also can be toggled by pressing p.')
args = parser.parse_args()

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

        self.lock = Lock()
        self.cubes = collections.defaultdict(lambda: collections.deque(maxlen=args.buffer_size))
        self.colormap = {}
        self.snapshots_observed = 0
        self.snapshots_rendered = 0
        self.percentage_mode = args.percentages
        self.cpu_cubes = []
        self.cpu_cluster_cubes = []
        self.cpumode = args.cpu

        self.cpu_color = Color.green if args.color == Color.mixed else args.color
        self.gpu_color = Color.blue if args.color == Color.mixed else args.color
        self.ane_color = Color.red if args.color == Color.mixed else args.color
        self.cells = self._cells()
        self.stdscr = stdscr

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

    def process_snapshot(self, m):
        initcolormap = not self.colormap
        
        with self.lock:
            for cluster in m['processor']['clusters']:
                idle_cluster, total_cluster = 0.0, 0.0
                cluster_title = f'{cluster["name"]} total CPU util'
                if not cluster_title in self.cubes:
                    self.cubes[cluster_title] = collections.deque(maxlen=args.buffer_size)
                    self.cpu_cluster_cubes.append(cluster_title)
                    self.colormap[cluster_title] = self.cpu_color
                for cpu in cluster['cpus']:
                    title = f'{cluster["name"]} CPU {cpu["cpu"]} util'
                    self.cubes[title].append(100.0 - 100.0 * cpu['idle_ratio'])
                    if initcolormap:
                        self.cpu_cubes.append(title)
                        self.colormap[title] = self.cpu_color
                    idle_cluster += cpu['idle_ratio']
                    total_cluster += 1.0
                
                self.cubes[cluster_title].append(100.0 - 100.0 * idle_cluster / total_cluster)
                    
            self.cubes['GPU util'].append(100.0 - 100.0 * m['gpu']['idle_ratio'])
            ane_scaling = 8.0 * args.refresh_ms
            self.cubes['ANE util'].append(100.0 * m['processor']['ane_energy'] / ane_scaling)
            if initcolormap:
                self.colormap['GPU util'] = self.gpu_color
                self.colormap['ANE util'] = self.ane_color
            self.snapshots_observed += 1

    def render(self, stdscr):
        with self.lock:
            if self.snapshots_observed == self.snapshots_rendered:
                return
        stdscr.erase()
        rows, cols = stdscr.getmaxyx()
        spacing = ' ' * spacing_width

        filter_cpu = lambda it : self.cpumode == CPUMode.all or (self.cpumode == CPUMode.by_cluster and it[0] not in self.cpu_cubes) or (self.cpumode == CPUMode.by_core and it[0] not in self.cpu_cluster_cubes)

        with self.lock:
            for i, (title, series) in enumerate(filter(filter_cpu, self.cubes.items())):
                cells = self.cells[self.colormap[title]]
                range = len(cells)
            
                if rows <= i * 2 + 2 or cols <= 3:
                    break

                titlestr = f'╔{spacing}{title}'
                stdscr.addstr(i * 2, 0, titlestr)
                stdscr.addstr(i * 2 + 1, 0, '╚')
                
                strvalue = f'last:{series[-1]:3.0f}%{spacing}╗' if self.percentage_mode == Percentages.last else f'{spacing}╗'
                stdscr.addstr(i * 2, cols - len(strvalue), strvalue)
                stdscr.addstr(i * 2 + 1, cols - spacing_width - 1, f'{spacing}╝')

                title_filling = filling * (cols - len(strvalue) - len(titlestr))
                stdscr.addstr(i * 2, len(titlestr), title_filling)

                index = max(0, len(series) - (cols - 2 * spacing_width - 2))
                data_slice = list(itertools.islice(series, index, None))

                clamp = lambda v, a, b: int(max(a, min(v, b)))
                cell = lambda v: cells[clamp(round(v * range / 100.0), 0, range - 1)]
                
                for j, v in enumerate(data_slice):
                    chr, color_pair = cell(v)
                    stdscr.addstr(i * 2 + 1, cols - len(data_slice) + j - 1 - spacing_width, chr, curses.color_pair(color_pair))
                self.snapshots_rendered += 1
        stdscr.refresh()

    def loop(self, powermetrics, firstline):
        buf = bytearray()
        buf.extend(firstline)
        def reader():
            while True:
                line = powermetrics.stdout.readline()
                buf.extend(line)
                if b'</plist>\n' == line:
                    self.process_snapshot(plistlib.loads(bytes(buf).strip(b'\x00')))
                    buf.clear()

        reader_thread = Thread(target=reader, daemon=True)
        reader_thread.start()

        while True:
            self.render(self.stdscr)
            key = self.stdscr.getch()
            if key == ord('q') or key == ord('Q'):
                exit(0)
            if key == ord('p'):
                with self.lock:
                    self.percentage_mode = self.percentage_mode.other()
            if key == ord('c'):
                with self.lock:
                    self.cpumode = self.cpumode.next()


def main(stdscr, powermetrics, firstline=''):
    h = Horizon(stdscr)
    h.loop(powermetrics, firstline)

if __name__ == '__main__':
    cmd = ['sudo', 'powermetrics', '-f', 'plist', '-i', str(args.refresh_ms), '-s', 'cpu_power,gpu_power,ane_power']
    powermetrics = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    line = powermetrics.stdout.readline()
    curses.wrapper(main, powermetrics, line)