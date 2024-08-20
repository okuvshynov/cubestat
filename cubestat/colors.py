import curses

from cubestat.common import DisplayMode


class ColorTheme(DisplayMode):
    mono = 'mono'
    inv = 'inv'
    col = 'col'


colors_ansi256 = {
    'green': [-1, 150, 107, 22],
    'red':   [-1, 224, 181, 138],
    'blue':  [-1, 189, 146, 103],
    'pink':  [-1, 223, 180, 137],
    'gray':  [-1, 7, 8, 0],
    'white': [-1, 8, 7, 15],
}

light_colormap = {
    'cpu':     'green',
    'ram':     'pink',
    'gpu':     'red',
    'ane':     'red',
    'disk':    'blue',
    'network': 'blue',
    'swap':    'pink',
    'power':   'red',
}


def prepare_cells():
    chrs = [' ', '▁', '▂', '▃', '▄', '▅', '▆', '▇', '█']
    cells = {}
    colorpair = 1
    for name, colors in colors_ansi256.items():
        cells[name] = []
        for i, (fg, bg) in enumerate(zip(colors[1:], colors[:-1])):
            curses.init_pair(colorpair, fg, bg)
            j = 0 if i == 0 else 1
            cells[name].extend((chr, colorpair) for chr in chrs[j:])
            colorpair += 1
    return cells


def get_theme(metric, color_mode):
    res = {
        ColorTheme.mono: 'gray',
        ColorTheme.inv:  'white',
        ColorTheme.col:  light_colormap.get(metric, 'green')
    }
    return res[color_mode]
