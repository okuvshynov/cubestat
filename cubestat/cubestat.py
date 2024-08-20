#!/usr/bin/env python3

import argparse
import curses
import logging

from threading import Thread, Lock

from cubestat.common import DisplayMode
from cubestat.colors import get_theme, ColorTheme
from cubestat.input import InputHandler
from cubestat.data import DataManager
from cubestat.screen import Screen

from cubestat.platforms.factory import get_platform
from cubestat.metrics_registry import get_metrics, metrics_configure_argparse


class ViewMode(DisplayMode):
    off = "off"
    one = "one"
    all = "all"


class Cubestat:
    def __init__(self, stdscr, args):
        self.screen = Screen(stdscr)
        self.ruler_interval = 20  # chars

        self.lock = Lock()

        self.snapshots_observed = 0
        self.snapshots_rendered = 0
        self.settings_changed = False
        self.v_shift = 0
        self.h_shift = 0

        self.view = ViewMode.one
        self.theme = ColorTheme.col

        self.refresh_ms = args.refresh_ms
        self.step_s = args.refresh_ms / 1000.0
        self.metrics = get_metrics(args)

        self.input_handler = InputHandler(self)
        self.data_manager = DataManager(args.buffer_size)

    def do_read(self, context) -> None:
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

    def max_val(self, metric, title: str, data_slice: list) -> float:
        max_value, _ = metric.format(title, data_slice, [-1])
        return max_value

    def _ruler_values(self, metric, title: str, idxs: list, data: list) -> list:
        if self.view == ViewMode.off:
            return []
        idxs = [idx for idx in idxs if idx < len(data)]
        data_indices = [-idx - 1 for idx in idxs]
        _, formatted_values = metric.format(title, data, data_indices)
        if self.view == ViewMode.one and len(idxs) > 1:
            idxs = idxs[:1]
        return list(zip(idxs, formatted_values))

    def render(self) -> None:
        with self.lock:
            if self.snapshots_rendered > self.snapshots_observed:
                logging.fatal('self.snapshots_rendered > self.snapshots_observed')
                exit(0)
            if self.snapshots_observed == self.snapshots_rendered and not self.settings_changed:
                return

        self.screen.render_start()
        cols = self.screen.cols
        ruler_indices = list(range(0, cols, self.ruler_interval))
        base_ruler = "." * cols

        row = 0
        with self.lock:
            skip = self.v_shift
            for metric_name, title, series in self.data_manager.data_gen():
                metric = self.metrics[metric_name]
                show, indent = metric.pre(title)

                if not show:
                    continue

                if skip > 0:
                    skip -= 1
                    continue

                chart_width = self.screen.chart_width(indent)
                data_slice = self.data_manager.get_slice(series, self.h_shift, chart_width)
                ruler_values = self._ruler_values(metric, title, ruler_indices, data_slice)

                self.screen.render_ruler(indent, title, base_ruler, ruler_values, row)

                max_value = self.max_val(metric, title, data_slice)
                theme = get_theme(metric_name, self.theme)
                self.screen.render_chart(theme, max_value, data_slice, row)

                row += 2
            self.snapshots_rendered = self.snapshots_observed
            self.settings_changed = False
            if self.view != ViewMode.off:
                ruler_times = [(i, f'-{(self.step_s * (i + self.h_shift)):.2f}s') for i in ruler_indices]
                self.screen.render_time(base_ruler, ruler_times, row)
        self.screen.render_done()

    def loop(self, platform):
        Thread(target=platform.loop, daemon=True, args=(self.do_read,)).start()
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
    parser.add_argument(
        '--refresh_ms', '-i', type=int, default=1000,
        help='Update frequency (milliseconds)'
    )

    parser.add_argument(
        '--buffer_size', type=int, default=500,
        help='Number of datapoints to store. Consider setting it larger than the screen width to accommodate window resizing.'
    )

    parser.add_argument(
        '--view', type=ViewMode, default=ViewMode.one, choices=list(ViewMode),
        help='Display mode (legend, values, time). Hotkey: "v".'
    )

    metrics_configure_argparse(parser)
    args = parser.parse_args()
    curses.wrapper(start, get_platform(args.refresh_ms), args)


if __name__ == '__main__':
    main()
