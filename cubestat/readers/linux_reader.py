import time

class LinuxReader:
    def __init__(self, interval_ms):
        self.interval_ms = interval_ms
        self.platform    = 'linux'

    def loop(self, do_read_cb):
        # TODO: should this be monotonic?
        begin_ts = time.time()
        n = 0
        d = self.interval_ms / 1000.0
        while True:
            do_read_cb()
            n += 1
            expected_time = begin_ts + n * d
            current_time = time.time()
            if expected_time > current_time:
                time.sleep(expected_time - current_time)
