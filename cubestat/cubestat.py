#!/usr/bin/env python3

import argparse
import collections
import curses
import itertools
import plistlib
import subprocess
import time
import sys
import psutil

from importlib.util import find_spec
from enum import Enum
from math import floor
from threading import Thread, Lock

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

parser = argparse.ArgumentParser("cubestat")
parser.add_argument('--refresh_ms', '-i', type=int, default=1000, help='Update frequency, milliseconds')
parser.add_argument('--buffer_size', type=int, default=500, help='How many datapoints to store. Having it larger than screen width is a good idea as terminal window can be resized')
parser.add_argument('--cpu', type=CPUMode, default=CPUMode.all, choices=list(CPUMode), help='CPU mode - showing all cores, only cumulative by cluster or both. Can be toggled by pressing c.')
parser.add_argument('--color', type=Color, default=Color.mixed, choices=list(Color))
parser.add_argument('--percentages', type=Percentages, default=Percentages.last, choices=list(Percentages), help='Show/hide numeric utilization percentage. Can be toggled by pressing p.')
parser.add_argument('--disk', action="store_true", default=True, help="Show disk read/write. Can be toggled by pressing d.")
parser.add_argument('--network', action="store_true", default=True, help="Show network io. Can be toggled by pressing n.")
parser.add_argument('--no-disk', action="store_false", dest="disk", help="Hide disk read/write. Can be toggled by pressing d.")
parser.add_argument('--no-network', action="store_false", dest="network", help="Hide network io. Can be toggled by pressing n.")

args = parser.parse_args()

def snapshot_base():
    return {
        'cpu': {},
        'accelerators': {},
        'ram': {'RAM used %': psutil.virtual_memory().percent},
        'disk': {},
        'network': {},
    }

# psutil + nvsmi for nVidia GPU
class LinuxReader:
    def __init__(self, interval_ms):
        self.has_nvidia = False
        self.first = True
        self.interval_ms = interval_ms
        try:
            subprocess.check_output('nvidia-smi')
            nvspec = find_spec('pynvml')
            if nvspec is not None:
                from pynvml.smi import nvidia_smi
                self.nvsmi = nvidia_smi.getInstance()
                self.has_nvidia = True
        except Exception:
            # TODO: add logging here
            pass

    def read(self):
        res = snapshot_base()

        disk_load = psutil.disk_io_counters()
        disk_read_kb = disk_load.read_bytes / 2 ** 10
        disk_written_kb = disk_load.write_bytes / 2 ** 10
        nw_load = psutil.net_io_counters()
        nw_read_kb = nw_load.bytes_recv / 2 ** 10
        nw_written_kb = nw_load.bytes_sent / 2 ** 10
        d = self.interval_ms / 1000.0

        cpu_clusters = []

        cluster_title = 'Total CPU util %'
        cpu_clusters.append(cluster_title)
        total_load = 0.0
        res['cpu'][cluster_title] = 0.0

        cpu_load = psutil.cpu_percent(percpu=True)
        for i, v in enumerate(cpu_load):
            title = f'CPU {i} util %'
            res['cpu'][title] = v
            total_load += v
        res['cpu'][cluster_title] = total_load / len(cpu_load)

        if self.has_nvidia:
            for i, v in enumerate(self.nvsmi.DeviceQuery('utilization.gpu,memory.total,memory.used')['gpu']):
                res['accelerators'][f'GPU {i} util %'] = v['utilization']['gpu_util']
                res['accelerators'][f'GPU {i} memory used %'] = v['fb_memory_usage']['used'] / v['fb_memory_usage']['total']

        if self.first:
            self.disk_read_last = disk_read_kb
            self.disk_written_last = disk_written_kb
            self.network_read_last = nw_read_kb
            self.network_written_last = nw_written_kb
            self.first = False

        res['disk']['disk read KB/s'] = ((disk_read_kb - self.disk_read_last) / d)
        res['disk']['disk write KB/s'] = ((disk_written_kb - self.disk_written_last) / d)
        self.disk_read_last = disk_read_kb
        self.disk_written_last = disk_written_kb

        res['network']['network i KB/s'] = ((nw_read_kb - self.network_read_last) / d)
        res['network']['network w KB/s'] = ((nw_written_kb - self.network_written_last) / d)
        self.network_read_last = nw_read_kb
        self.network_written_last = nw_written_kb
        return res.items(), cpu_clusters

class AppleReader:
    def __init__(self, interval_ms) -> None:
        self.interval_ms = interval_ms

    def read(self, snapshot):
        res = snapshot_base()

        cpu_clusters = []
        for cluster in snapshot['processor']['clusters']:
            idle_cluster, total_cluster = 0.0, 0.0
            cluster_title = f'{cluster["name"]} total CPU util %'
            cpu_clusters.append(cluster_title)
            res['cpu'][cluster_title] = 0.0
            for cpu in cluster['cpus']:
                title = f'{cluster["name"]} CPU {cpu["cpu"]} util %'
                res['cpu'][title] = 100.0 - 100.0 * cpu['idle_ratio']
                idle_cluster += cpu['idle_ratio']
                total_cluster += 1.0
            res['cpu'][cluster_title] = 100.0 - 100.0 * idle_cluster / total_cluster

        res['accelerators']['GPU util %'] = 100.0 - 100.0 * snapshot['gpu']['idle_ratio']
        ane_scaling = 8.0 * self.interval_ms
        res['accelerators']['ANE util %'] = 100.0 * snapshot['processor']['ane_energy'] / ane_scaling

        res['disk']['disk read'] = snapshot['disk']['rbytes_per_s']
        res['disk']['disk write'] = snapshot['disk']['wbytes_per_s']
        res['network']['network rx'] = snapshot['network']['ibyte_rate']
        res['network']['network tx'] = snapshot['network']['obyte_rate']
        return res.items(), cpu_clusters

# settings

class Horizon:
    def __init__(self, stdscr, reader):
        stdscr.nodelay(False)
        stdscr.timeout(50)
        curses.curs_set(0)
        curses.start_color()
        curses.use_default_colors()

        self.spacing_width = 1
        self.filling = '.'
        self.colorschemes = {
            Color.green: [-1, 150, 107, 22],
            Color.red: [-1, 224, 181, 138],
            Color.blue: [-1, 189, 146, 103],
        }

        self.cells = self.prepare_cells()
        self.stdscr = stdscr

        # all of the fields below are mutable and can be accessed from 2 threads
        self.lock = Lock()
        self.data = {k: collections.defaultdict(lambda: collections.deque(maxlen=args.buffer_size)) for k in ['cpu', 'accelerators', 'ram', 'disk', 'network']}
        self.colormap = {
            'cpu': Color.green if args.color == Color.mixed else args.color,
            'ram': Color.green if args.color == Color.mixed else args.color,
            'accelerators': Color.red if args.color == Color.mixed else args.color,
            'disk': Color.blue if args.color == Color.mixed else args.color,
            'network': Color.blue if args.color == Color.mixed else args.color,
        }
        self.snapshots_observed = 0
        self.snapshots_rendered = 0
        self.percentage_mode = args.percentages
        self.cpumode = args.cpu
        self.show_disk = args.disk
        self.show_network = args.network
        self.settings_changed = False
        self.reader = reader
        self.vertical_shift = 0


    def prepare_cells(self):
        chrs = [' ', '▁', '▂', '▃', '▄', '▅', '▆', '▇', '█']
        cells = {}
        colorpair = 1
        for name, colors in self.colorschemes.items():
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

    def write_string(self, r, c, s, color=0):
        if r < 0 or r >= self.rows or c < 0:
            return
        if c + len(s) > self.cols:
            s = s[:self.cols - c]
        try:
            self.stdscr.addstr(r, c, s, color)
        except:
            pass

    def wc(self, r, c, chr, color=0):
        if r < 0 or r >= self.rows or c < 0 or c >= self.cols:
            return
        try:
            self.stdscr.addch(r, c, chr, color)
        except:
            pass

    def render(self):
        with self.lock:
            if self.snapshots_observed == self.snapshots_rendered and not self.settings_changed:
                return
        self.stdscr.erase()
        self.rows, self.cols = self.stdscr.getmaxyx()
        spacing = ' ' * self.spacing_width

        with self.lock:
            i = 0
            skip = self.vertical_shift
            for group_name, group in self.data.items():
                if group_name == 'disk' and not self.show_disk:
                    continue
                if group_name == 'network' and not self.show_network:
                    continue

                cells = self.cells[self.colormap[group_name]]
                range = len(cells)
                for title, series in group.items():
                    if skip > 0:
                        skip -= 1
                        continue
                    indent = ''

                    if group_name == 'cpu':
                        if self.cpumode == CPUMode.by_cluster and title not in self.cpu_clusters:
                            continue
                        if self.cpumode == CPUMode.by_core and title in self.cpu_clusters:
                            continue
                        if self.cpumode == CPUMode.all and title not in self.cpu_clusters:
                            indent = '  '
                    titlestr = f'{indent}╔{spacing}{title}'
                    self.write_string(i * 2, 0, titlestr)
                    self.write_string(i * 2 + 1, 0, f'{indent}╚')
                    
                    index = max(0, len(series) - (self.cols - 2 * self.spacing_width - 2 - len(indent)))
                    data_slice = list(itertools.islice(series, index, None))

                    B = 100.0
                    strvalue = f'last:{data_slice[-1]:3.0f}%{spacing}╗' if self.percentage_mode == Percentages.last else f'{spacing}╗'
                    if group_name == 'disk' or group_name == 'network':
                        B = max(data_slice)
                        B = float(1 if B == 0 else 2 ** (int((B - 1)).bit_length()))
                        if B > 1024 * 1024: # Mb/s
                            strvalue =  f'last:{data_slice[-1] / (1024 * 1024) :3.0f}|{int(B / (1024 * 1024))}Mb/s{spacing}╗' if self.percentage_mode == Percentages.last else f'{spacing}╗'
                        elif B > 1024: # Kb/s
                            strvalue =  f'last:{data_slice[-1] / 1024:3.0f}|{int(B / 1024)}Kb/s{spacing}╗' if self.percentage_mode == Percentages.last else f'{spacing}╗'
                        else:
                            strvalue =  f'last:{data_slice[-1]:3.0f}|{int(B)}bytes/s{spacing}╗' if self.percentage_mode == Percentages.last else f'{spacing}╗'

                    title_filling = self.filling * (self.cols - len(strvalue) - len(titlestr))
                    self.write_string(i * 2, len(titlestr), title_filling)
                    self.write_string(i * 2, self.cols - len(strvalue), strvalue)

                    border = f'{spacing}╝'
                    self.write_string(i * 2 + 1, self.cols - len(border), border)

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
                        self.wc(i * 2 + 1, col, chr, curses.color_pair(color_pair))

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


    def reader_loop_linux(self):
        begin_ts = time.time()
        n = 0
        d = args.refresh_ms / 1000.0
        while True:
            snapshot, cpu_clusters = self.reader.read()
            self.process_snapshot(snapshot, cpu_clusters)
            n += 1
            expected_time = begin_ts + n * d
            time.sleep(expected_time - time.time())

    def reader_loop_apple(self, powermetrics, firstline):
        buf = bytearray()
        buf.extend(firstline)

        while True:
            line = powermetrics.stdout.readline()
            buf.extend(line)
            # we check for </plist> rather than '0x00' because powermetrics injects 0x00 
            # right before the measurement (in time), not right after. So, if we were to wait 
            # for 0x00 we'll be delaying next sample by sampling period. 
            if b'</plist>\n' == line:
                snapshot, cpu_clusters = self.reader.read(plistlib.loads(bytes(buf).strip(b'\x00')))
                self.process_snapshot(snapshot, cpu_clusters)
                buf.clear()

    def loop(self, reader, *args):
        reader_thread = Thread(target=reader, daemon=True, args=args)
        reader_thread.start()
        self.render_loop()

def start_apple(stdscr, powermetrics, firstline):
    h = Horizon(stdscr, AppleReader(args.refresh_ms))
    h.loop(h.reader_loop_apple, powermetrics, firstline)

def start_linux(stdscr):
    h = Horizon(stdscr, LinuxReader(args.refresh_ms))
    h.loop(h.reader_loop_linux)

def main():
    if sys.platform == "darwin":
        cmd = ['sudo', 'powermetrics', '-f', 'plist', '-i', str(args.refresh_ms), '-s', 'cpu_power,gpu_power,ane_power,network,disk']
        powermetrics = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # we are getting first line here to allow user to enter sudo credentials before 
        # curses initialization.
        line = powermetrics.stdout.readline()
        curses.wrapper(start_apple, powermetrics, line)
    if sys.platform == "linux" or sys.platform == "linux2":
        curses.wrapper(start_linux)

if __name__ == '__main__':
    main()
