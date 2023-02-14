import sys

# TODO:
# -- add options
#  - keep reading (like tail -f)
#  - range options (min/max), (0/max), etc.
#  - squash vs rotate vs newline
#  - two lines mode

def horizon_line(series, cells):
    if not series:
        return ''
    range = len(cells)
    (a, b) = min(series), max(series)
    a = 0
    if a == b:
        b = a + 1
    clamp = lambda v, a, b: max(a, min(v, b))
    cell = lambda v: cells[clamp(int((v - a) * range / (b - a)), 0, range - 1)]
    return ''.join([cell(v) for v in series]) + f' {series[-1]:.3f}'

if __name__ == '__main__':
    chr = [' ', '▁', '▂', '▃', '▄', '▅', '▆', '▇', '█']
    rst = '\033[0m'
    colors = [231, 194, 150, 107, 64, 22]
    fg = [f'\33[38;5;{c}m' for c in colors]
    bg = [f'\33[48;5;{c}m' for c in colors]
    cells = [f'{f}{b}{c}{rst}' for f, b in zip(fg[1:], bg[:-1]) for c in chr]
    cells.append(f'{bg[-1]}{fg[0]} {rst}')

    v = [float(x.strip()) for x in sys.stdin.readlines() if x.strip() != '']

    width = 150

    if len(v) > width:
        w = (len(v) - 1) // width + 1
        v = [sum(v[i:(i + w)]) / len(v[i:i+w]) for  i in range(0, len(v), w)]  

    print(horizon_line(v, cells))
