from cubestat.common import EnumStr

import curses

class Color(EnumStr):
    red = 'red'
    green = 'green'
    blue = 'blue'
    pink = 'pink'

# TODO: should this be defined in the metric as well?
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

def get_scheme(metric):
    return light_colormap.get(metric, Color.green)
