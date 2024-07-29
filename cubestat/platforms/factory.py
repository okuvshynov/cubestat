import sys

from cubestat.platforms.linux import LinuxPlatform
from cubestat.platforms.macos import MacOSPlatform

def get_platform(refresh_ms):
    if sys.platform == "darwin":
        return MacOSPlatform(refresh_ms)
    if sys.platform == "linux" or sys.platform == "linux2":
        return LinuxPlatform(refresh_ms)
    logging.fatal(f'platform {sys.platform} is not supported yet.')
