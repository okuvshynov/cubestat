import re
import subprocess

# for macos
class SwapUsageReader:
    def __init__(self):
        pass

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

    def read(self):
        res = {}
        try:
            swap_stats = subprocess.run(["sysctl", "vm.swapusage"], capture_output=True, text=True)
            tokens = swap_stats.stdout.strip().split(' ')
            res['swap used'] = self.parse_memstr(tokens[7])
        except:
            # log something
            pass
        return res