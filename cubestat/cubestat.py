#!/usr/bin/env python3

import plistlib
import subprocess
import curses
import argparse
import collections
import itertools
from threading import Thread, Lock
from enum import Enum

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
    mixed = 'mixed'

parser = argparse.ArgumentParser("./cubestat.py")
parser.add_argument('--refresh_ms', '-i', type=int, default=500, help='Update frequency, milliseconds')
parser.add_argument('--buffer_size', type=int, default=500, help='How many datapoints to store. Having it larger than screen width is a good idea as terminal window can be resized')
parser.add_argument('--cpu', type=CPUMode, default=CPUMode.by_core, choices=list(CPUMode), help='CPU mode - showing all cores, only cumulative by cluster or both. Can be toggled by pressing c.')
parser.add_argument('--color', type=Color, default=Color.mixed, choices=list(Color))
parser.add_argument('--percentages', type=Percentages, default=Percentages.hidden, choices=list(Percentages), help='Show/hide numeric utilization percentage. Can be toggled by pressing p.')
args = parser.parse_args()

# settings
spacing_width = 1
filling = '.'
disk_limit_mb = 5000
network_limit_mb = 5000
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
        self.gpu_color = Color.blue if args.color == Color.mixed else args.color
        self.ane_color = Color.red if args.color == Color.mixed else args.color
        self.io_color = Color.green if args.color == Color.mixed else args.color
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
        self.show_disk = False
        self.show_network = False
        self.settings_changes = False

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
                cluster_title = f'{cluster["name"]} total CPU util %'
                if not cluster_title in self.cubes:
                    self.cubes[cluster_title] = collections.deque(maxlen=args.buffer_size)
                    self.cpu_cluster_cubes.append(cluster_title)
                    self.colormap[cluster_title] = self.cpu_color
                for cpu in cluster['cpus']:
                    title = f'{cluster["name"]} CPU {cpu["cpu"]} util %'
                    self.cubes[title].append(100.0 - 100.0 * cpu['idle_ratio'])
                    if initcolormap:
                        self.cpu_cubes.append(title)
                        self.colormap[title] = self.cpu_color
                    idle_cluster += cpu['idle_ratio']
                    total_cluster += 1.0
                self.cubes[cluster_title].append(100.0 - 100.0 * idle_cluster / total_cluster)
                    
            self.cubes['GPU util %'].append(100.0 - 100.0 * m['gpu']['idle_ratio'])
            ane_scaling = 8.0 * args.refresh_ms
            self.cubes['ANE util %'].append(100.0 * m['processor']['ane_energy'] / ane_scaling)
            if initcolormap:
                self.colormap['GPU util %'] = self.gpu_color
                self.colormap['ANE util %'] = self.ane_color

            self.cubes['network i MB/s'].append(m['network']['ibyte_rate'] / (2 ** 20))
            self.cubes['network o MB/s'].append(m['network']['obyte_rate'] / (2 ** 20))
            self.cubes['disk read MB/s'].append(m['disk']['rbytes_per_s'] / (2 ** 20))
            self.cubes['disk write MB/s'].append(m['disk']['wbytes_per_s'] / (2 ** 20))
            if initcolormap:
                self.colormap['network i MB/s'] = self.io_color
                self.colormap['network o MB/s'] = self.io_color
                self.colormap['disk read MB/s'] = self.io_color
                self.colormap['disk write MB/s'] = self.io_color

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

    def render(self):
        with self.lock:
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
                if 'disk' in title and not self.show_disk:
                    continue
                if 'network' in title and not self.show_network:
                    continue
                cells = self.cells[self.colormap[title]]
                range = len(cells)

                # indent is used to highlight cores which belong to the same cluster (efficiency vs performance).
                indent = '  ' if self.cpumode == CPUMode.all and title in self.cpu_cubes else ''

                titlestr = f'{indent}╔{spacing}{title}'      
                self.wl(i * 2, 0, titlestr)
                self.wl(i * 2 + 1, 0, f'{indent}╚')
                
                strvalue = f'last:{series[-1]:3.0f}{spacing}╗' if self.percentage_mode == Percentages.last else f'{spacing}╗'
                self.wr(i * 2, 0, strvalue)
                self.wr(i * 2 + 1, 0, f'{spacing}╝')

                title_filling = filling * (self.cols - len(strvalue) - len(titlestr))
                self.wl(i * 2, len(titlestr), title_filling)

                index = max(0, len(series) - (self.cols - 2 * spacing_width - 2 - len(indent)))
                data_slice = list(itertools.islice(series, index, None))

                clamp = lambda v, a, b: int(max(a, min(v, b)))
                B = disk_limit_mb if 'disk' in title else network_limit_mb if 'network' in title else 100.0    
                cell = lambda v: cells[clamp(round(v * range / B), 0, range - 1)]
                
                for j, v in enumerate(data_slice):
                    chr, color_pair = cell(v)
                    self.wr(i * 2 + 1, len(data_slice) - j + spacing_width, chr, curses.color_pair(color_pair))
                self.snapshots_rendered += 1
        self.stdscr.refresh()

    def loop(self, powermetrics, firstline):
        buf = bytearray()
        buf.extend(firstline)

        def reader():
            while True:
                line = powermetrics.stdout.readline()
                buf.extend(line)
                # we check for </plist> rather than '0x00' because powermetrics injects 0x00 
                # right before the measurement (in time), not right after. So, if we were to wait 
                # for 0x00 we'll be delaying next sample by sampling period. 
                if b'</plist>\n' == line:
                    self.process_snapshot(plistlib.loads(bytes(buf).strip(b'\x00')))
                    buf.clear()
        reader_thread = Thread(target=reader, daemon=True)
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

def start(stdscr, powermetrics, firstline):
    h = Horizon(stdscr)
    h.loop(powermetrics, firstline)

def main():
    cmd = ['sudo', 'powermetrics', '-f', 'plist', '-i', str(args.refresh_ms), '-s', 'cpu_power,gpu_power,ane_power,network,disk']
    powermetrics = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    line = powermetrics.stdout.readline()
    curses.wrapper(start, powermetrics, line)

if __name__ == '__main__':
    main()