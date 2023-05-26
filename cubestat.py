import plistlib
import subprocess
import logging
import select

logging.basicConfig(format='%(asctime)s %(message)s', filename='/tmp/cubestat.log', level=logging.INFO)

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
    return ''.join([cell(v) for v in series]) + f' {series[-1]:.1f}'

def collect_metrics(m):
    res = {}
    res['gpu util %'] = 100.0 - 100.0 * m['gpu']['idle_ratio']

    # is 10000 right here?
    res['ane_util %'] = 100.0 * m['processor']['ane_energy'] / 10000.0
    res['nw i kbytes/s'] = m['network']['ibyte_rate'] / 1024.0
    res['nw o kbytes/s'] = m['network']['obyte_rate'] / 1024.0
    res['disk r kbytes/s'] = m['disk']['rbytes_per_s'] / 1024.0
    res['disk w kbytes/s'] = m['disk']['wbytes_per_s'] / 1024.0

    for cluster in m['processor']['clusters']:
        for cpu in cluster['cpus']:
            res[f'{cluster["name"]} cpu {cpu["cpu"]} util %'] = 100.0 - 100.0 * cpu['idle_ratio']

    return res

auto_domains = ['ane_energy', 'nw i kbytes/s', 'nw o kbytes/s', 'disk r kbytes/s', 'disk w kbytes/s']
all_cells = get_cells()
cubes = {}
width = 150

def append_data(new_point):
    for k, v in new_point.items():
        if k not in cubes.keys():
            cubes[k] = [v]
        else:
            cubes[k].append(v)
            if (len(cubes[k]) > width):
                cubes[k] = cubes[k][1:]

def render():
    print('\n' * 10)
    print('-' * width)
    for k, v in cubes.items():
        print(k)
        domain = (0.0, None) if k in auto_domains else (0.0, 100.0)
        print(horizon_line(v, domain, all_cells))

def start():
    cmd = ['sudo', 'powermetrics', '-f', 'plist', '-i', '1000']

    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    buf = bytearray()

    while True:
        read_ready, _, _ = select.select([p.stdout], [], [])

        buf.extend(p.stdout.readline())
        if b'</plist>\n' in buf:
            snapshots = bytes(buf).strip(b'\x00').split(b'\x00')
            if not snapshots[-1].endswith(b'</plist>\n'):
                buf = bytearray(snapshots.pop())
            else:
                buf = bytearray()

            for s in snapshots:
                append_data(collect_metrics(plistlib.loads(s)))
            render()

        if p.poll() != None:
            break

if __name__ == '__main__':
    start()
