import psutil

# based on psutil
class MemReader:
    def __init__(self, interval_ms):
        pass

    def read(self):
        res = {
            'ram': {'RAM used %': psutil.virtual_memory().percent},
        }
        return res