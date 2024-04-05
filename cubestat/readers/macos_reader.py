import subprocess
import plistlib

from cubestat.readers.mem_reader import MemReader
from cubestat.readers.swapusage_reader import SwapUsageReader

# reading from powermetrics
class AppleReader:
    # This is pretty much a guess based on tests on a few models I had available.
    # Need anything M3 + Ultra models to test.
    # Based on TOPS numbers Apple published, all models seem to have some ANE 
    # except Ultra having 2x.
    ane_power_scalers = {
        "M1": 13000.0,
        "M2": 15500.0,
        "M3": 15500.0,
    }

    def __init__(self, interval_ms) -> None:
        # identity the model to get ANE power scaler
        brand_str = subprocess.check_output(['sysctl', '-n', 'machdep.cpu.brand_string'], text=True)
        self.ane_scaler = 15500 # default to M2
        for k, v in self.ane_power_scalers.items():
            if k in brand_str:
                self.ane_scaler = v
                if 'Ultra' in brand_str:
                    self.ane_scaler *= 2
                break
        
        cmd = ['sudo', 'powermetrics', '-f', 'plist', '-i', str(interval_ms), '-s', 'cpu_power,gpu_power,ane_power,network,disk']
        self.powermetrics = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # we are getting first line here to allow user to enter sudo credentials before 
        # curses initialization.
        self.firstline = self.powermetrics.stdout.readline()

        self.mem_reader = MemReader(interval_ms)
        self.swap_reader = SwapUsageReader()

    def read(self, snapshot):
        res = self.mem_reader.read()
        res['swap'] = self.swap_reader.read()

        cpu_clusters = []
        for cluster in snapshot['processor']['clusters']:
            idle_cluster, total_cluster = 0.0, 0.0
            n_cpus = len(cluster['cpus'])
            cluster_title = f'[{n_cpus}] {cluster["name"]} total CPU util %'
            cpu_clusters.append(cluster_title)
            res['cpu'][cluster_title] = 0.0
            for cpu in cluster['cpus']:
                title = f'{cluster["name"]} CPU {cpu["cpu"]} util %'
                res['cpu'][title] = 100.0 - 100.0 * cpu['idle_ratio']
                idle_cluster += cpu['idle_ratio']
                total_cluster += 1.0
            res['cpu'][cluster_title] = 100.0 - 100.0 * idle_cluster / total_cluster

        res['gpu']['GPU util %'] = 100.0 - 100.0 * snapshot['gpu']['idle_ratio']
        
        res['ane']['ANE util %'] = 100.0 * snapshot['processor']['ane_energy'] / self.ane_scaler

        res['disk']['disk read'] = snapshot['disk']['rbytes_per_s']
        res['disk']['disk write'] = snapshot['disk']['wbytes_per_s']
        res['network']['network rx'] = snapshot['network']['ibyte_rate']
        res['network']['network tx'] = snapshot['network']['obyte_rate']
        return res.items(), cpu_clusters
    
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
                snapshot, cpu_clusters = self.read(plistlib.loads(bytes(buf).strip(b'\x00')))
                on_snapshot_cb(snapshot, cpu_clusters)
                buf.clear()