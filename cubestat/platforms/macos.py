import subprocess
import plistlib

class MacOSPlatform:
    def __init__(self, interval_ms) -> None:
        cmd = ['sudo', 'powermetrics', '-f', 'plist', '-i', str(interval_ms), '-s', 'cpu_power,gpu_power,ane_power,network,disk']
        self.powermetrics = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # we are getting first line here to allow user to enter sudo credentials before 
        # curses initialization.
        self.firstline = self.powermetrics.stdout.readline()
        self.platform = 'macos'
    
    def loop(self, do_read_cb):
        buf = bytearray()
        buf.extend(self.firstline)

        while True:
            line = self.powermetrics.stdout.readline()
            buf.extend(line)
            # we check for </plist> rather than '0x00' because powermetrics injects 0x00 
            # right before the measurement event, not right after. So, if we were to wait 
            # for 0x00 we'll be delaying next sample by sampling period. 
            if b'</plist>\n' == line:
                context = plistlib.loads(bytes(buf).strip(b'\x00'))
                do_read_cb(context)
                buf.clear()
