def plot_timeline(width: int, char_ms: int, fill: str, W: int, shift: int = 0) -> str:
    interval_ms = char_ms * W

    mult = {
        'ms': 1,
        's' : 1000
    }

    for unit, m in reversed(mult.items()):
        if m <= interval_ms:
            break

    res = ""
    d = - (interval_ms + char_ms * shift) / m
    while len(res) + W <= width:
        res = f'|{d:.1f}{unit}'.ljust(W, fill) + res
        d -= interval_ms / m
    return res.rjust(width, fill)