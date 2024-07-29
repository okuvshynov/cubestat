#!/usr/bin/env python3

import argparse
import curses
import logging

from math import floor
from threading import Thread, Lock

from cubestat.common import DisplayMode
from cubestat.colors import get_theme, ColorTheme
from cubestat.input import InputHandler
from cubestat.data import DataManager
from cubestat.screen import Screen

from cubestat.platforms.factory import get_platform

from cubestat.metrics.registry import get_metrics, metrics_configure_argparse
from cubestat.metrics import cpu, gpu, memory, accel, swap, network, disk, power

class ViewMode(DisplayMode):
    off = "off"
    one = "one"
    all = "all"

class Cubestat:
    def __init__(self, stdscr, args):
        self.screen = Screen(stdscr)
        self.timeline_interval = 20 # chars

        self.lock = Lock()

        self.snapshots_observed = 0
        self.snapshots_rendered = 0
        self.settings_changed = False
        self.v_shift = 0
        self.h_shift = 0

        self.view = ViewMode.one
        self.theme = ColorTheme.col

        self.refresh_ms = args.refresh_ms
        self.metrics = get_metrics(args)

        self.input_handler = InputHandler(self)
        self.data_manager  = DataManager(args.buffer_size)

    def do_read(self, context):
        updates = []
        for group, metric in self.metrics.items():
            datapoint = metric.read(context)
            for title, value in datapoint.items():
                updates.append((group, title, value))

        with self.lock:
            self.data_manager.update(updates)
            self.snapshots_observed += 1
            if self.h_shift > 0:
                self.h_shift += 1

    def max_val(self, group_name, title, data_slice):
        max_value, _ = self.metrics[group_name].format(title, data_slice, [-1])
        return max_value
    
    def format_value(self, group_name, title, data_slice, idx):
        _, values = self.metrics[group_name].format(title, data_slice, [idx])
        return f'{values[0]}' if self.view != ViewMode.off else ''
    
    def inject_to_string(self, string, at, val):
        pos = self.screen.cols - 1 - len(self.screen.spacing) - 1 - at
        if pos > len(val):
            return string[:pos - len(val)] + val + "|" + string[pos + 1:]
        return string
    
    def vertical_time(self, at, curr_line):
        time_s = (self.refresh_ms * (at + self.h_shift)) / 1000.0
        time_str = f'-{time_s:.2f}s'
        return self.inject_to_string(curr_line, at, time_str)
    
    def vertical_val(self, group_name, title, at, data_slice, curr_line):
        if at >= len(data_slice):
            return curr_line
        data_index = - at - 1
        v = self.format_value(group_name, title, data_slice, data_index)
        return self.inject_to_string(curr_line, at, v)

    def render(self):
        with self.lock:
            if self.snapshots_rendered > self.snapshots_observed:
                logging.fatal('self.snapshots_rendered > self.snapshots_observed')
                exit(0)
            if self.snapshots_observed == self.snapshots_rendered and not self.settings_changed:
                return
        
        self.screen.render_start()

        cols = self.screen.cols

        base_line = "." * cols

        row = 0
        with self.lock:
            skip = self.v_shift
            for group_name, title, series in self.data_manager.data_gen():
                show, indent = self.metrics[group_name].pre(title)

                if not show:
                    continue
                
                if skip > 0:
                    skip -= 1
                    continue

                data_slice = self.data_manager.get_slice(series, indent, self.h_shift, cols, self.screen.spacing)
                max_value = self.max_val(group_name, title, data_slice)
                theme     = get_theme(group_name, self.theme)

                curr_line = base_line
                if self.view != ViewMode.off:
                    for ago in range(0, cols, self.timeline_interval):
                        curr_line = self.vertical_val(group_name, title, ago, data_slice, curr_line)
                        if self.view != ViewMode.all:
                            break
                
                self.screen.render_legend(indent, title, curr_line, row)
                self.screen.render_chart(theme, max_value, data_slice, row)

                row += 2
            self.snapshots_rendered = self.snapshots_observed
            self.settings_changed   = False
            if self.view != ViewMode.off:
                curr_line = base_line
                for ago in range(0, cols, self.timeline_interval):
                    curr_line = self.vertical_time(ago, curr_line)
                curr_line = curr_line[len(self.screen.spacing) + 1:  - len(self.screen.spacing) - 1]
        self.screen.render_done()

    def loop(self, platform):
        t = Thread(target=platform.loop, daemon=True, args=[self.do_read])
        t.start()
        self.screen.stdscr.keypad(True)
        while True:
            self.render()
            self.input_handler.handle_input()

def start(stdscr, platform, args):
    h = Cubestat(stdscr, args)
    h.loop(platform)

def main():
    logging.basicConfig(filename='/tmp/cubestat.log', level=logging.INFO)
    parser = argparse.ArgumentParser("cubestat")
    parser.add_argument('--refresh_ms', '-i', type=int, default=1000, help='Update frequency, milliseconds')
    parser.add_argument('--buffer_size', type=int, default=500, help='How many datapoints to store. Having it larger than screen width is a good idea as terminal window can be resized')
    parser.add_argument('--view', type=ViewMode, default=ViewMode.one, choices=list(ViewMode), help='legend/values/time mode. Can be toggled by pressing v.')

    metrics_configure_argparse(parser)
    args = parser.parse_args()
    curses.wrapper(start, get_platform(args.refresh_ms), args)

if __name__ == '__main__':
    main()
