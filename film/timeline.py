"""One source of truth for the edit: cut times (frame-exact at 24 fps) and the three words.

The cuts accelerate like breathing that quickens: 1 s holds, then ~0.55 s, ~0.42 s, ~0.33 s,
and a final run shrinking from 0.25 s to 0.17 s, ending hard at 16.0 s on the end card.
"""
import numpy as np

FPS = 24
DUR = 20.0
END = 16.0          # hard cut to the end card
LOGO = 17.3         # the wordmark resolves


def _q(t): return round(t * FPS) / FPS


def _cuts():
    t = [0.0, 1.30, 2.30, 3.30, 4.30]
    for step, until in ((0.55, 8.15), (0.42, 10.25), (0.33, 12.56)):
        while t[-1] + step <= until + 1e-6: t.append(t[-1] + step)
    # final run: intervals shrink linearly, scaled to land exactly on END
    n = 16; iv = np.linspace(0.25, 0.17, n); iv *= (END - t[-1]) / iv.sum()
    for d in iv[:-1]: t.append(t[-1] + d)
    return sorted({_q(x) for x in t})


CUTS = _cuts()                       # shot i runs CUTS[i] .. CUTS[i+1] (last one until END)
SHOT_ENDS = CUTS[1:] + [END]
WORDS = [(_q(8.57), _q(10.25), 'Untangle'), (_q(10.25), _q(12.56), 'how things'), (_q(12.56), END, 'work.')]

if __name__ == '__main__':
    print(len(CUTS), 'shots'); print([round(c, 3) for c in CUTS]); print(np.round(np.diff(CUTS + [END]), 3))
