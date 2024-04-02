import subprocess

class FreeSwapReader:
    def __init__(self):
        pass

    def read(self):
        res = {}
        try:
            swap_stats = subprocess.run(["free", "-b"], capture_output=True, text=True)
            lines = swap_stats.stdout.splitlines()
            for l in lines:
                if l.startswith("Swap:"):
                    parts = l.split()
                    res['swap used'] = float(parts[2])
        except:
            # TODO: log something
            pass

        return res
        