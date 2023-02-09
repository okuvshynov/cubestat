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

def horizon_line(series, domain, cells):
    if not series:
        return ''
    range = len(cells)
    (a, b) = domain
    if b is None:
        b = max(series)
    if a == b:
        b = a + 1
    clamp = lambda v, a, b: max(a, min(v, b))
    cell = lambda v: cells[clamp(int((v - a) * range / (b - a)), 0, range - 1)]
    return ''.join([cell(v) for v in series]) + f' {series[-1]:.3f}'

def collect_metrics(m):
    res = {}
    res['gpu util %'] = 1.0 - m['gpu']['idle_ratio']
    res['ane_energy'] = m['processor']['ane_energy']
    res['nw i kbytes/s'] = m['network']['ibyte_rate'] / 1024.0
    res['nw o kbytes/s'] = m['network']['obyte_rate'] / 1024.0
    res['disk r kbytes/s'] = m['disk']['rbytes_per_s'] / 1024.0
    res['disk w kbytes/s'] = m['disk']['wbytes_per_s'] / 1024.0

    for cluster in m['processor']['clusters']:
        for cpu in cluster['cpus']:
            res[f'{cluster["name"]} cpu {cpu["cpu"]} util %'] = 1.0 - cpu['idle_ratio']

    return res

auto_domains = ['ane_energy', 'nw i kbytes/s', 'nw o kbytes/s', 'disk r kbytes/s', 'disk w kbytes/s']
all_cells = get_cells()
cubes = {}
width = 80

def append_data(new_point):
    for k, v in new_point.items():
        if k not in cubes.keys():
            cubes[k] = [v]
        else:
            cubes[k].append(v)
            if (len(cubes[k]) > width):
                cubes[k] = cubes[k][1:]

def render():
    print('-' * width)
    for k, v in cubes.items():
        print(k)
        domain = (0.0, None) if k in auto_domains else (0.0, 1.0)
        print(horizon_line(v, domain, all_cells))

def start():
    cmd = ['sudo', 'powermetrics', '-f', 'plist', '-o', '/tmp/cubestat', '-i', '5000']
    try:
        os.remove('/tmp/cubestat')
    except FileNotFoundError:
        pass

    subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    while True:
        try:
            curr = bytearray()
            with open('/tmp/cubestat', 'rb') as f:
                while True:
                    data = f.read(2 ** 20)
                    curr.extend(data)
                    if b'</plist>\n' in curr:
                        readings = bytes(curr).split(b'\x00')
                        if not readings[-1].endswith(b'</plist>\n'):
                            curr = bytearray(readings.pop())
                        else:
                            curr = bytearray()

                        for r in readings:
                            if r:
                                append_data(collect_metrics(plistlib.loads(r)))
                        render()
                    else:
                        time.sleep(0.05)

        except FileNotFoundError:
            time.sleep(0.05)

if __name__ == '__main__':
    start()