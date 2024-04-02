import subprocess
import plistlib

from readers.mem_reader import MemReader
from readers.swapusage_reader import SwapUsageReader

# reading from powermetrics
class AppleReader:
    # these scalers are based on running mock convnet from scripts/apple_loadgen.py
    # TODO: this is different for different models. Need to run tests on different models.
    ane_power_scalers_mw = {
        'Mac14,2': 15000.0, # M2 MacBook Air
        'Macmini9,1': 13000.0, # M1 Mac Mini
    }

    def __init__(self, interval_ms) -> None:
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

        hw_model = snapshot["hw_model"]

        cpu_clusters = []
        for cluster in snapshot['processor']['clusters']:
            idle_cluster, total_cluster = 0.0, 0.0
            cluster_title = f'{cluster["name"]} total CPU util %'
            cpu_clusters.append(cluster_title)
            res['cpu'][cluster_title] = 0.0
            for cpu in cluster['cpus']:
                title = f'{cluster["name"]} CPU {cpu["cpu"]} util %'
                res['cpu'][title] = 100.0 - 100.0 * cpu['idle_ratio']
                idle_cluster += cpu['idle_ratio']
                total_cluster += 1.0
            res['cpu'][cluster_title] = 100.0 - 100.0 * idle_cluster / total_cluster

        res['accelerators']['GPU util %'] = 100.0 - 100.0 * snapshot['gpu']['idle_ratio']
        
        ane_scaling = AppleReader.ane_power_scalers_mw.get(hw_model, 15000.0)
        res['accelerators']['ANE util %'] = 100.0 * snapshot['processor']['ane_energy'] / ane_scaling

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