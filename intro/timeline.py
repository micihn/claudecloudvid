"""One source of truth for the 35 s intro: every time the picture and the score share.

Three acts:
  LENS     0.0 - PUSH     eight archive images seen through a lens, dissolving, each pushing in
  PUSH     PUSH - HORIZ   the camera goes through the lens; its rim opens into a horizon
  HORIZON  HORIZ - END    match-cuts on one horizon, accelerating; three phrases above the arc
  END      END - DUR      dark card, a brand-lit limb: "A digital atelier", then the wordmark
"""
import numpy as np

FPS = 24
DUR = 35.0
PUSH = 11.0          # the push through the lens starts
HORIZ = 13.0         # the horizon is open: first match-cut shot
END = 27.0           # hard cut to the end card
ATELIER = 27.4       # "A digital atelier"
LOGO = 30.2          # the wordmark


def _q(t): return round(t * FPS) / FPS


# lens: images change every 1.4 s with a 0.5 s dissolve; the first fades up from black
LENS = [_q(0.2 + 1.4 * i) for i in range(8)]
LENS_X = 0.5


def _cuts():
    # holds shrink from 1.05 s to 0.25 s, scaled to land exactly on END
    n = 24; iv = np.geomspace(1.05, 0.25, n); iv *= (END - HORIZ) / iv.sum()
    t = [HORIZ]
    for d in iv[:-1]: t.append(t[-1] + d)
    return sorted({_q(x) for x in t})


CUTS = _cuts()                       # horizon shot i runs CUTS[i] .. CUTS[i+1] (last one until END)
_w = lambda t: min(CUTS, key=lambda c: abs(c - t))     # phrases change on a cut
WORDS = [(_w(16.3), _w(20.0), 'Untangle'), (_w(20.0), _w(23.5), 'how things'), (_w(23.5), END, 'really work.')]

if __name__ == '__main__':
    print('lens', LENS)
    print(len(CUTS), 'horizon shots'); print([round(c, 3) for c in CUTS]); print(np.round(np.diff(CUTS + [END]), 3))
    print(WORDS)
