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
from time import sleep

logging.basicConfig(filename='/tmp/cubestat.log')

class CPUMode(Enum):
    collapsed = 'collapsed'
    expanded = 'expanded'
    cluster = 'cluster'

    def __str__(self):
        return self.value
    
class Color(Enum):
    red = 'red'
    green = 'green'
    blue = 'blue'
    mixed = 'mixed'

    def __str__(self):
        return self.value


parser = argparse.ArgumentParser("cubestate monitoring")
parser.add_argument('--refresh_ms', '-i', type=int, default=500)
parser.add_argument('--buffer_size', type=int, default=500)
parser.add_argument('--cpu', type=CPUMode, default=CPUMode.expanded, choices=list(CPUMode))
parser.add_argument('--color', type=Color, default=Color.mixed, choices=list(Color))
args = parser.parse_args()

spacing_width = 1
filling = '.'

auto_domains = ['nw i kbytes/s', 'nw o kbytes/s', 'disk r kbytes/s', 'disk w kbytes/s']
cpu_color = Color.red if args.color == Color.mixed else args.color
gpu_ane_color = Color.blue if args.color == Color.mixed else args.color
io_color = Color.green if args.color == Color.mixed else args.color

# these are mutable
cubelock = Lock()
cubes = collections.defaultdict(lambda: collections.deque(maxlen=args.buffer_size))
colormap = {}

colorschemes = {
    Color.green: [-1, 150, 107, 22],
    Color.red: [-1, 224, 138, 52],
    Color.blue: [-1, 189, 103, 17],
}

def gen_cells():
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

def process_snapshot(m):
    initcolormap = not colormap
    
    idle, total = 0.0, 0.0
    
    with cubelock:
        for cluster in m['processor']['clusters']:
            for cpu in cluster['cpus']:
                if args.cpu == CPUMode.expanded:
                    cubes[f'{cluster["name"]} cpu {cpu["cpu"]} util %'].append(100.0 - 100.0 * cpu['idle_ratio'])
                    if initcolormap:
                        colormap[f'{cluster["name"]} cpu {cpu["cpu"]} util %'] = cpu_color
                else:
                    idle += cpu['idle_ratio']
                    total += 1.0
            if args.cpu == CPUMode.cluster:
                cubes[f'{cluster["name"]} total cpu util %'].append(100.0 - 100.0 * idle / total)
                if initcolormap:
                    colormap[f'{cluster["name"]} total cpu util %'] = cpu_color
                idle, total = 0.0, 0.0
                
            if args.cpu == CPUMode.collapsed:
                cubes[f'total cpu util %'].append(100.0 - 100.0 * idle / total)
                if initcolormap:
                    colormap[f'total cpu util %'] = cpu_color

        cubes['GPU util %'].append(100.0 - 100.0 * m['gpu']['idle_ratio'])
        cubes['ANE util %'].append(100.0 * m['processor']['ane_energy'] / 10000.0)
        if initcolormap:
            colormap['GPU util %'] = gpu_ane_color
            colormap['ANE util %'] = gpu_ane_color

        cubes['nw i kbytes/s'].append(m['network']['ibyte_rate'] / 1024.0)
        cubes['nw o kbytes/s'].append(m['network']['obyte_rate'] / 1024.0)
        cubes['disk r kbytes/s'].append(m['disk']['rbytes_per_s'] / 1024.0)
        cubes['disk w kbytes/s'].append(m['disk']['wbytes_per_s'] / 1024.0)

        colormap['nw i kbytes/s'] = io_color
        colormap['nw o kbytes/s'] = io_color
        colormap['disk r kbytes/s'] = io_color
        colormap['disk w kbytes/s'] = io_color

def render(stdscr, cellsmap):
    stdscr.erase()
    rows, cols = stdscr.getmaxyx()
    spacing = ' ' * spacing_width

    with cubelock:
        for i, (title, series) in enumerate(cubes.items()):
            cells = cellsmap[colormap[title]]
            range = len(cells)
        
            if rows <= i * 2 + 1 or cols <= 3:
                break

            titlestr = f'╔{spacing}{title}'
            stdscr.addstr(i * 2, 0, titlestr)
            stdscr.addstr(i * 2 + 1, 0, '╚')
            
            strvalue = f'{series[-1]:.1f}{spacing}╗'
            stdscr.addstr(i * 2, cols - len(strvalue), strvalue)
            stdscr.addstr(i * 2 + 1, cols - spacing_width - 1, f'{spacing}╝')

            title_filling = filling * (cols - len(strvalue) - len(titlestr))
            stdscr.addstr(i * 2, len(titlestr), title_filling)

            index = max(0, len(series) - (cols - 2 * spacing_width - 2))
            data_slice = list(itertools.islice(series, index, None))
            b = max(1, max(data_slice)) if title in auto_domains else 100.0

            clamp = lambda v, a, b: max(a, min(v, b))
            cell = lambda v: cells[clamp(int(v * range / b), 0, range - 1)]
            
            for j, v in enumerate(data_slice):
                chr, color_pair = cell(v)
                stdscr.addstr(i * 2 + 1, j + 1 + spacing_width, chr, curses.color_pair(color_pair))
    stdscr.refresh()

def main(stdscr, powermetrics):
    stdscr.nodelay(True)
    curses.curs_set(0)
    curses.start_color()
    curses.use_default_colors()
    
    buf = bytearray()
    cells = gen_cells()

    def reader():
        while True:
            line = powermetrics.stdout.readline()
            buf.extend(line)
            if b'</plist>\n' == line:
                process_snapshot(plistlib.loads(bytes(buf).strip(b'\x00')))
                buf.clear()

    reader_thread = Thread(target=reader, daemon=True)
    reader_thread.start()

    while True:
        render(stdscr, cells)
        key = stdscr.getch()
        if key == ord('q') or key == ord('Q'):
            exit(0)
        sleep(0.005)

if __name__ == '__main__':
    cmd = ['sudo', 'powermetrics', '-f', 'plist', '-i', str(args.refresh_ms)]
    powermetrics = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    curses.wrapper(main, powermetrics)