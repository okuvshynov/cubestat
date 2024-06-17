import subprocess
import plistlib

from cubestat.readers.mem_reader import MemReader

def get_ane_scaler() -> float:
    # This is pretty much a guess based on tests on a few models I had available.
    # Need anything M3 + Ultra models to test.
    # Based on TOPS numbers Apple published, all models seem to have same ANE 
    # except Ultra having 2x.
    ane_power_scalers = {
        "M1": 13000.0,
        "M2": 15500.0,
        "M3": 15500.0,
    }
    # identity the model to get ANE scaler
    brand_str = subprocess.check_output(['sysctl', '-n', 'machdep.cpu.brand_string'], text=True)
    ane_scaler = 15500 # default to M2
    for k, v in ane_power_scalers.items():
        if k in brand_str:
            ane_scaler = v
            if 'ultra' in brand_str.lower():
                ane_scaler *= 2
            break
    return ane_scaler

class AppleReader:
    def __init__(self, interval_ms) -> None:
        self.ane_scaler = get_ane_scaler()

        cmd = ['sudo', 'powermetrics', '-f', 'plist', '-i', str(interval_ms), '-s', 'cpu_power,gpu_power,ane_power,network,disk']
        self.powermetrics = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # we are getting first line here to allow user to enter sudo credentials before 
        # curses initialization.
        self.firstline = self.powermetrics.stdout.readline()

        self.mem_reader = MemReader(interval_ms)
        self.platform = 'macos'

    def read(self, snapshot):
        res = self.mem_reader.read()
        
        res['gpu']['GPU util %'] = 100.0 - 100.0 * snapshot['gpu']['idle_ratio']
        res['ane']['ANE util %'] = 100.0 * snapshot['processor']['ane_power'] / self.ane_scaler

        res['power']['total power']  = snapshot['processor']['combined_power']
        res['power']['ANE power']    = snapshot['processor']['ane_power']
        res['power']['CPU power']    = snapshot['processor']['cpu_power']
        res['power']['GPU power']    = snapshot['processor']['gpu_power']

        return res.items()
    
    def loop(self, on_snapshot_cb):
        buf = bytearray()
        buf.extend(self.firstline)

        while True:
            line = self.powermetrics.stdout.readline()
            buf.extend(line)
            # we check for </plist> rather than '0x00' because powermetrics injects 0x00 
            # right before the measurement event, not right after. So, if we were to wait 
            # for 0x00 we'll be delaying next sample by sampling period. 
            if b'</plist>\n' == line:
                data = plistlib.loads(bytes(buf).strip(b'\x00'))
                snapshot = self.read(data)
                on_snapshot_cb(snapshot, data)
                buf.clear()