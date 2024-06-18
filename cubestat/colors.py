from cubestat.common import EnumStr

import curses

class Color(EnumStr):
    red = 'red'
    green = 'green'
    blue = 'blue'
    pink = 'pink'
    olive = 'olive'
    navy = 'navy'
    blue_dark = 'blue_dark'
    purple = 'purple'
    mixed = 'mixed'
    dark = 'dark'

dark_colormap = {
    'cpu': Color.purple,
    'ram': Color.navy,
    'gpu': Color.blue_dark,
    'ane': Color.blue_dark,
    'disk': Color.olive,
    'network': Color.olive,
    'swap': Color.navy,
    'power': Color.blue_dark,
}

light_colormap = {
    'cpu': Color.green,
    'ram': Color.pink,
    'gpu': Color.red,
    'ane': Color.red,
    'disk': Color.blue,
    'network': Color.blue,
    'swap': Color.pink,
    'power': Color.red,
}

colors_ansi256 = {
    Color.green: [-1, 150, 107, 22],
    Color.red: [-1, 224, 181, 138],
    Color.blue: [-1, 189, 146, 103],
    Color.pink: [-1, 223, 180, 137],
    Color.olive: [-1, 58, 101, 144],
    Color.navy: [-1, 18, 61, 105],
    Color.blue_dark: [-1, 23, 66, 109],
    Color.purple: [-1, 53, 96, 138]
}

def prepare_cells():
    chrs = [' ', '▁', '▂', '▃', '▄', '▅', '▆', '▇', '█']
    cells = {}
    colorpair = 1
    for name, colors in colors_ansi256.items():
        cells[name] = []
        for fg, bg in zip(colors[1:], colors[:-1]):
            curses.init_pair(colorpair, fg, bg)
            cells[name].extend((chr, colorpair) for chr in chrs)
            colorpair += 1
    return cells