import logging
import re
import subprocess

from cubestat.metrics.base_metric import base_metric
from cubestat.metrics_registry import cubestat_metric
from cubestat.common import SimpleMode, label_bytes


class swap_metric(base_metric):
    def pre(self, title):
        if self.mode == SimpleMode.hide:
            return False, ''
        return True, ''

    def format(self, title, values, idxs):
        return label_bytes(values, idxs)

    @classmethod
    def key(cls):
        return 'swap'

    @classmethod
    def configure_argparse(cls, parser):
        parser.add_argument(
            '--swap',
            type=SimpleMode,
            default=SimpleMode.show,
            choices=list(SimpleMode),
            help='swap show/hide. Hotkey: "s"'
        )

    def configure(self, conf):
        self.mode = conf.swap
        return self

    def hotkey(self):
        return 's'


@cubestat_metric('darwin')
class macos_swap_metric(swap_metric):
    def _parse_memstr(self, size_str):
        match = re.match(r"(\d+(\.\d+)?)([KMG]?)", size_str)
        if not match:
            raise ValueError("Invalid memory size format")
        number, _, unit = match.groups()
        number = float(number)

        if unit == "G":
            return number * 1024 * 1024 * 1024
        elif unit == "M":
            return number * 1024 * 1024
        elif unit == "K":
            return number * 1024
        else:
            return number

    def read(self, _context):
        res = {}
        try:
            swap_stats = subprocess.run(["sysctl", "vm.swapusage"], capture_output=True, text=True)
            swap_stats.check_returncode()  # Raise CalledProcessError if exit status is non-zero
            tokens = swap_stats.stdout.strip().split(' ')
            if len(tokens) < 8:
                raise IndexError("Invalid sysctl output")
            res['swap used'] = self._parse_memstr(tokens[7])
        except subprocess.CalledProcessError as e:
            logging.error(f"sysctl command failed: {e}")
        except IndexError as e:
            logging.error(f"Invalid sysctl output: {e}")
        except Exception as e:
            logging.error(f"Unexpected error: {e}")

        return res


@cubestat_metric('linux')
class linux_swap_metric(swap_metric):
    def read(self, _context):
        with open('/proc/meminfo', 'r') as file:
            meminfo = file.readlines()

        swap_total = 0
        swap_free = 0

        for line in meminfo:
            if 'SwapTotal:' in line:
                swap_total = int(line.split()[1])
            if 'SwapFree:' in line:
                swap_free = int(line.split()[1])

        return {'swap used': 1024 * float(swap_total - swap_free)}
