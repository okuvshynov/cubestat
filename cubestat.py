#!/usr/bin/env python3

import plistlib
import subprocess
import curses
import argparse
import collections
import itertools
import logging

logging.basicConfig(filename='/tmp/cubestat.log')

parser = argparse.ArgumentParser("cubestate monitoring")
parser.add_argument('--refresh_ms', '-i', type=int, default=500)
parser.add_argument('--buffer_size', type=int, default=500)
args = parser.parse_args()

spacing_width = 1
filling = '.'

auto_domains = ['nw i kbytes/s', 'nw o kbytes/s', 'disk r kbytes/s', 'disk w kbytes/s']
cubes = collections.defaultdict(lambda: collections.deque(maxlen=args.buffer_size))
colormap = {}

colorschemes = {
    'green5': [-1, 194, 150, 107, 64, 22],
    'teal5': [-1, 195, 152, 109, 66, 23],
    'red5': [-1, 224, 181, 138, 95, 52],
    'green2': [-1, 10, 2],
    'red2': [-1, 9, 1],
    'blue2': [-1, 12, 4],
    'green3': [-1, 10, 2, 22],
    'red3': [-1, 9, 1, 52],
    'blue3': [-1, 12, 4, 17],
    'gray10': [-1, 254, 252, 250, 248, 246, 244, 242, 240, 238, 236],
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
    for cluster in m['processor']['clusters']:
        for cpu in cluster['cpus']:
            cubes[f'{cluster["name"]} cpu {cpu["cpu"]} util %'].append(100.0 - 100.0 * cpu['idle_ratio'])
            if initcolormap:
                colormap[f'{cluster["name"]} cpu {cpu["cpu"]} util %'] = 'gray10'
    cubes['GPU util %'].append(100.0 - 100.0 * m['gpu']['idle_ratio'])
    cubes['ANE util %'].append(100.0 * m['processor']['ane_energy'] / 10000.0)
    if initcolormap:
        colormap['GPU util %'] = 'gray10'
        colormap['ANE util %'] = 'gray10'

    cubes['nw i kbytes/s'].append(m['network']['ibyte_rate'] / 1024.0)
    cubes['nw o kbytes/s'].append(m['network']['obyte_rate'] / 1024.0)
    cubes['disk r kbytes/s'].append(m['disk']['rbytes_per_s'] / 1024.0)
    cubes['disk w kbytes/s'].append(m['disk']['wbytes_per_s'] / 1024.0)

    colormap['nw i kbytes/s'] = 'gray10'
    colormap['nw o kbytes/s'] = 'gray10'
    colormap['disk r kbytes/s'] = 'gray10'
    colormap['disk w kbytes/s'] = 'gray10'

def render(stdscr, cellsmap):
    stdscr.erase()
    rows, cols = stdscr.getmaxyx()
    spacing = ' ' * spacing_width
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

def main(stdscr):
    stdscr.nodelay(True)
    curses.curs_set(0)
    curses.start_color()
    curses.use_default_colors()
    
    cmd = ['sudo', 'powermetrics', '-f', 'plist', '-i', str(args.refresh_ms)]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    buf = bytearray()
    cells = gen_cells()

    while True:
        line = p.stdout.readline()
        buf.extend(line)
        if b'</plist>\n' == line:
            process_snapshot(plistlib.loads(bytes(buf).strip(b'\x00')))
            buf.clear()
            render(stdscr, cells)

if __name__ == '__main__':
    curses.wrapper(main)