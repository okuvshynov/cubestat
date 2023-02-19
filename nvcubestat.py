import itertools
import sys
import os
import time
from pynvml.smi import nvidia_smi

# a version of cubestat which polls data from nvidia_smi
# and shows per-GPU utilization

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

all_cells = get_cells()
cubes = {}
width = 80
freq_ms = 1000

if __name__ == '__main__':
    nvsmi = nvidia_smi.getInstance()
    started = time.time()
    delay = freq_ms / 1000.0
    v = None
    for it in itertools.count(start=0):
        res = nvsmi.DeviceQuery('utilization.gpu')
        if v is None:
            v = [[] for _ in res['gpu']]
        for i in range(len(res['gpu'])):
            v[i].append(res['gpu'][i]['utilization']['gpu_util'])
            if len(v[i]) > width:
                v[i] = v[i][1:]
            print(horizon_line(v[i], (0.0, 100.0), all_cells))
        passed = time.time() - started
        expected_to_pass = it * delay
        to_sleep = delay - (passed - expected_to_pass)
        if to_sleep > 0:
            time.sleep(to_sleep)
