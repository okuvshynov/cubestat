import itertools
import sys
import os
import time
from pynvml.smi import nvidia_smi

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
freq_ms = 500

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
        print(horizon_line(v, (0.0, 100.0), all_cells))

# we treat ',' ' ' the same
if __name__ == '__main__':
    nvsmi = nvidia_smi.getInstance()
    started = time.time()
    delay = freq_ms / 1000.0
    for i in itertools.count(start=0):
        res = nvsmi.DeviceQuery('utilization.gpu')
        gpu_util = res['gpu'][0]['utilization']['gpu_util']
        append_data({'gpu_util': gpu_util})
        render()
        passed = time.time() - started
        expected_to_pass = i * delay
        time.sleep(delay - (passed - expected_to_pass))
