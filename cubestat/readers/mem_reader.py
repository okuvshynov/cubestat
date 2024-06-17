import psutil

# based on psutil
class MemReader:
    def __init__(self, interval_ms):
        self.first = True
        self.interval_ms = interval_ms

    # TODO: make this return only memory
    def read(self):
        res = {
            'ram': {'RAM used %': psutil.virtual_memory().percent},
            'gpu': {},
            'ane': {},
            'network': {},
            'power': {},
        }
        return res