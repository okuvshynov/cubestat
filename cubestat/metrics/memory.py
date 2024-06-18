import psutil

class ram_metric:
    def __init__(self, platform) -> None:
        if platform == 'linux':
            self.read = self.read_linux
        if platform == 'macos':
            self.read = self.read_macos

    def read_macos(self, _context):
        return {'RAM used %': psutil.virtual_memory().percent}
    
    def read_linux(self, _context):
        return {'RAM used %': psutil.virtual_memory().percent}
    
    def pre(self, mode, title):
        return True, ''