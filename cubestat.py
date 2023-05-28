#!/usr/bin/env python3

import plistlib
import subprocess
import curses
import argparse
import collections

parser = argparse.ArgumentParser("cubestate monitoring")
parser.add_argument('--refresh_ms', '-i', type=int, default=1000)
parser.add_argument('--width', '-w', type=int, default=80)
args = parser.parse_args()

auto_domains = ['nw i kbytes/s', 'nw o kbytes/s', 'disk r kbytes/s', 'disk w kbytes/s']
cubes = collections.defaultdict(lambda: collections.deque(maxlen=args.width))

def gen_cells():
    chrs = [' ', '▁', '▂', '▃', '▄', '▅', '▆', '▇', '█']
    colors = [-1, 194, 150, 107, 64, 22]
    cells = []
    for i, (fg, bg) in enumerate(zip(colors[1:], colors[:-1])):
        curses.init_pair(i + 1, fg, bg)
        cells.extend((chr, i + 1) for chr in chrs)
    return cells

def process_snapshot(m):
    cubes['gpu util %'].append(100.0 - 100.0 * m['gpu']['idle_ratio'])
    cubes['ane util %'].append(100.0 * m['processor']['ane_energy'] / 10000.0)
    cubes['nw i kbytes/s'].append(m['network']['ibyte_rate'] / 1024.0)
    cubes['nw o kbytes/s'].append(m['network']['obyte_rate'] / 1024.0)
    cubes['disk r kbytes/s'].append(m['disk']['rbytes_per_s'] / 1024.0)
    cubes['disk w kbytes/s'].append(m['disk']['wbytes_per_s'] / 1024.0)

    for cluster in m['processor']['clusters']:
        for cpu in cluster['cpus']:
            cubes[f'{cluster["name"]} cpu {cpu["cpu"]} util %'].append(100.0 - 100.0 * cpu['idle_ratio'])

def render(stdscr, cells):
    stdscr.clear()
    range = len(cells)
    for i, (k, series) in enumerate(cubes.items()):
        stdscr.addstr(i * 2, 0, '╔ ' + k)
        stdscr.addstr(i * 2 + 1, 0, '╚')
        
        b = max(1, max(series)) if k in auto_domains else 100.0
        clamp = lambda v, a, b: max(a, min(v, b))
        cell = lambda v: cells[clamp(int(v * range / b), 0, range - 1)]
        for j, v in enumerate(series):
            chr, color_pair = cell(v)
            stdscr.addstr(i * 2 + 1, 2 + j, chr, curses.color_pair(color_pair))
        
        stdscr.addstr(i * 2 + 1, 2 + len(series), f' {series[-1]:.1f}')

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
        buf.extend(p.stdout.readline())
        if b'</plist>\n' in buf:
            snapshots = bytes(buf).strip(b'\x00').split(b'\x00')
            if not snapshots[-1].endswith(b'</plist>\n'):
                buf = bytearray(snapshots.pop())
            else:
                buf = bytearray()

            for s in snapshots:
                process_snapshot(plistlib.loads(s))
            render(stdscr, cells)

if __name__ == '__main__':
    curses.wrapper(main)