import psutil

# based on psutil
class MemReader:
    def __init__(self, interval_ms):
        self.first = True
        self.interval_ms = interval_ms

    # TODO: make this return only memory
    def read(self):
        d = self.interval_ms / 1000.0
        res = {
            'cpu': {},
            'ram': {'RAM used %': psutil.virtual_memory().percent},
            'swap': {},
            'accelerators': {},
            'disk': {},
            'network': {},
        }
        return res