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
        except (curses.error, ValueError) as e:
            if isinstance(e, ValueError) and "Color number" in str(e):
                # Don't spam logs for each color attempt
                if i == 0:  # Only log once on first failure
                    logging.warning(
                        f'Terminal supports only {curses.COLORS} colors (256 needed for colors).'
                    )
                    logging.info('Falling back to monochrome mode.')
                    logging.info('For color support, try: export TERM=xterm-256color')
            else:
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
        self.fallback_to_mono = False
        colorpair = 1
        
        # Try to initialize color schemes
        for name, colors in colors_ansi256.items():
            cells, colorpair = cells_for_colorscheme(colors, colorpair)
            if cells is not None:
                self.schemes[name] = cells
            else:
                # If any color scheme fails, use monochrome for all
                self.fallback_to_mono = True
                break
        
        # Always add monochrome scheme
        self.schemes['mono'] = mono_cells()
        
        # If color initialization failed, use only monochrome
        if self.fallback_to_mono:
            logging.info('Using monochrome mode due to terminal limitations.')
            for name in colors_ansi256.keys():
                if name != 'mono':
                    self.schemes[name] = mono_cells()

    def get_cells(self, name):
        if name in self.schemes:
            return self.schemes[name]
        logging.error(f'requested colorscheme {name}.')
        return self.schemes['mono']
