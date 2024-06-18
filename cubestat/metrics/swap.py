import re
import subprocess

from cubestat.common import SimpleMode

class swap_metric:
    def __init__(self, platform):
        if platform == 'linux':
            self.read = self.read_linux
        if platform == 'macos':
            self.read = self.read_macos

    def parse_memstr(self, size_str):
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

    def read_macos(self, _context):
        res = {}
        try:
            swap_stats = subprocess.run(["sysctl", "vm.swapusage"], capture_output=True, text=True)
            tokens = swap_stats.stdout.strip().split(' ')
            res['swap used'] = self.parse_memstr(tokens[7])
        except:
            # log something
            pass
        return res
    
    def read_linux(self, _context):
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
    
    def pre(self, mode, title):
        if mode == SimpleMode.hide:
            return False, ''
        return True, ''