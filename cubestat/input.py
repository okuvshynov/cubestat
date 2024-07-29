import curses

class InputHandler:
    def __init__(self, horizon):
        self.horizon = horizon
        self.hotkeys = [(m.hotkey(), m) for m in self.horizon.metrics.values() if m.hotkey()]

    def handle_input(self):
        key = self.horizon.screen.stdscr.getch()
        if key == ord('q') or key == ord('Q'):
            exit(0)
        for k, metric in self.hotkeys:
            if key == ord(k):
                with self.horizon.lock:
                    metric.mode = metric.mode.next()
                    self.horizon.settings_changed = True
            if key == ord(k.upper()):
                with self.horizon.lock:
                    metric.mode = metric.mode.prev()
                    self.horizon.settings_changed = True
        if key == curses.KEY_UP:
            with self.horizon.lock:
                if self.horizon.v_shift > 0:
                    self.horizon.v_shift -= 1
                    self.horizon.settings_changed = True
        if key == curses.KEY_DOWN:
            with self.horizon.lock:
                self.horizon.v_shift += 1
                self.horizon.settings_changed = True
        if key == curses.KEY_LEFT:
            with self.horizon.lock:
                if self.horizon.h_shift + 1 < self.horizon.snapshots_observed:
                    self.horizon.h_shift += 1
                    self.horizon.settings_changed = True
        if key == curses.KEY_RIGHT:
            with self.horizon.lock:
                if self.horizon.h_shift > 0:
                    self.horizon.h_shift -= 1
                    self.horizon.settings_changed = True
        if key == ord('0'):
            with self.horizon.lock:
                if self.horizon.v_shift > 0:
                    self.horizon.v_shift = 0
                    self.horizon.settings_changed = True
                if self.horizon.h_shift > 0:
                    self.horizon.h_shift = 0
                    self.horizon.settings_changed = True
        if key == ord('v'):
            with self.horizon.lock:
                self.horizon.view = self.horizon.view.next()
                self.horizon.settings_changed = True
        if key == ord('V'):
            with self.horizon.lock:
                self.horizon.view = self.horizon.view.prev()
                self.horizon.settings_changed = True
        if key == ord('t'):
            with self.horizon.lock:
                self.horizon.theme = self.horizon.theme.next()
                self.horizon.settings_changed = True
        if key == ord('T'):
            with self.horizon.lock:
                self.horizon.theme = self.horizon.theme.prev()
                self.horizon.settings_changed = True
