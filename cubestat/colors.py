import curses
import logging

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


def mono_cells():
    chrs = [' ', '▁', '▂', '▃', '▄', '▅', '▆', '▇', '█']
    return [(c, 0) for c in chrs]


def cells_for_colorscheme(colors, colorpair):
    chrs = [' ', '▁', '▂', '▃', '▄', '▅', '▆', '▇', '█']
    res = []
    for i, (fg, bg) in enumerate(zip(colors[1:], colors[:-1])):
        try:
            curses.init_pair(colorpair, fg, bg)
        except curses.error:
            logging.error('curses.init_pair returned error.')
            logging.error('Consider setting up 256 colors terminal:')
            logging.error('  export TERM=xterm-256color')
            return None, colorpair
        j = 0 if i == 0 else 1
        res.extend((chr, colorpair) for chr in chrs[j:])
        colorpair += 1
    return res, colorpair


def get_theme(metric, color_mode):
    res = {
        ColorTheme.mono: 'gray',
        ColorTheme.inv:  'white',
        ColorTheme.col:  light_colormap.get(metric, 'green')
    }
    return res[color_mode]


class Colorschemes:
    def __init__(self):
        self.schemes = {}
        colorpair = 1
        for name, colors in colors_ansi256.items():
            cells, colorpair = cells_for_colorscheme(colors, colorpair)
            if cells is not None:
                self.schemes[name] = cells
        self.schemes['mono'] = mono_cells()

    def get_cells(self, name):
        if name in self.schemes:
            return self.schemes[name]
        logging.error(f'requested colorscheme {name}.')
        return self.schemes['mono']
