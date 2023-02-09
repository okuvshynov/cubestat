import os
import plistlib
import subprocess
import time

def get_cells():
    chr = [' ', '▁', '▂', '▃', '▄', '▅', '▆', '▇', '█']
    rst = '\033[0m'
    colors = [231, 194, 150, 107, 64, 22]
    fg = [f'\33[38;5;{c}m' for c in colors]
    bg = [f'\33[48;5;{c}m' for c in colors]
    res = [f'{f}{b}{c}{rst}' for f, b in zip(fg[1:], bg[:-1]) for c in chr]
    res.append(f'{bg[-1]}{fg[0]} {rst}')
    return res

def clamp(v, a, b):
    return max(a, min(v, b))

def horizon_line(series, domain, cells):
    range = len(cells)
    (va, vb) = domain
    if vb is None:
        vb = max(series)
    if va == vb:
        vb = va + 1
    cell = lambda v: cells[clamp(int((v - va) * range / (vb - va)), 0, range - 1)]
    return ''.join([cell(v) for v in series])

def collect_metrics(m):
    # add disk and network
    res = {}
    res['gpu util %'] = 1.0 - m['gpu']['idle_ratio']
    res['ane_energy'] = m['processor']['ane_energy']
    res['nw i bytes/s'] = m['network']['ibyte_rate']
    res['nw o bytes/s'] = m['network']['obyte_rate']
    res['disk r bytes/s'] = m['disk']['rbytes_per_s']
    res['disk w bytes/s'] = m['disk']['wbytes_per_s']

    for cluster in m['processor']['clusters']:
        name = cluster['name']
        for cpu in cluster['cpus']:
            res[f'{name} cpu {cpu["cpu"]} util %'] = 1.0 - cpu['idle_ratio']

    return res

auto_domains = ['ane_energy', 'nw i bytes/s', 'nw o bytes/s', 'disk r bytes/s', 'disk w bytes/s']

def append_data(data, new_point):
    for k, v in new_point.items():
        if k not in data.keys():
            data[k] = [v]
        else:
            data[k].append(v)
            if (len(data[k]) > 80):
                data[k] = data[k][1:]

def start():
    cmd = ['sudo', 'powermetrics', '-f', 'plist', '-o', '/tmp/cubestat', '-i', '1000']
    try:
        os.remove('/tmp/cubestat')
    except FileNotFoundError:
        pass

    cubes = {}
    all_cells = get_cells()
    subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    while True:
        try:
            curr = bytearray()
            with open('/tmp/cubestat', 'rb') as f:
                while True:
                    pos = f.tell()
                    data = f.read(1024)

                    if not data:
                        time.sleep(0.1)
                        f.seek(pos)
                    else:
                        curr.extend(data)

                        bcurr = bytes(curr)
                        if b'\x00' in bcurr:                        
                            readings = bcurr.split(b'\x00')
                            for r in readings[:-1]:
                                append_data(cubes, collect_metrics(plistlib.loads(r)))
                            
                            curr = bytearray(readings[-1])

                            for k, v in cubes.items():
                                print(k)
                                domain = (0.0, None) if k in auto_domains else (0.0, 1.0)
                                print(horizon_line(v, domain, all_cells))

        except FileNotFoundError:
            time.sleep(0.1)

if __name__ == '__main__':
    start()