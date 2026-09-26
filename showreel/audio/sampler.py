"""Tiny sampler for real recordings: load, normalise, repitch, place on a stereo bus."""
import os, re, glob, functools
import numpy as np, soundfile as sf
from scipy.signal import resample_poly, fftconvolve

SR = 48000
NOTE = {'C': 0, 'C#': 1, 'D': 2, 'D#': 3, 'E': 4, 'F': 5, 'F#': 6, 'G': 7, 'G#': 8, 'A': 9, 'A#': 10, 'B': 11}


@functools.lru_cache(maxsize=None)
def load(path):
    x, sr = sf.read(path, always_2d=True, dtype='float64')
    if x.shape[1] == 1: x = np.repeat(x, 2, 1)
    x = x[:, :2]
    if sr != SR:
        g = np.gcd(sr, SR); x = resample_poly(x, SR // g, sr // g, axis=0)
    # trim leading silence, remove DC, peak-normalise
    x = x - x.mean(0)
    a = np.abs(x).max(1); thr = a.max() * 0.02
    i0 = max(0, int(np.argmax(a > thr)) - int(0.002 * SR))
    x = x[i0:]
    # gate the room-noise tail: cut where the 20 ms envelope stays below -54 dB
    k = int(0.02 * SR); env = np.convolve(np.abs(x).max(1), np.ones(k) / k, 'same')
    above = np.where(env > env.max() * 0.002)[0]
    if len(above):
        end = min(len(x), above[-1] + k); x = x[:end].copy()
        f = min(end, int(0.06 * SR)); x[end - f:] *= np.linspace(1, 0, f)[:, None]
    return x / (np.abs(x).max() + 1e-9)


def yin_midi(x, fmin=40, fmax=2000):
    m = x.mean(1)
    seg = m[int(0.08 * SR): int(0.08 * SR) + 4096]
    if len(seg) < 4096: seg = m[:4096]
    W = 2048; tmin, tmax = SR // fmax, min(SR // fmin, W - 1)
    d = np.array([np.sum((seg[:W] - seg[t:t + W]) ** 2) for t in range(tmax + 1)])
    cm = d[1:] * np.arange(1, len(d)) / np.maximum(np.cumsum(d[1:]), 1e-12)
    cm = np.concatenate([[1], cm])
    cand = np.where(cm[tmin:] < 0.15)[0]
    tau = (cand[0] + tmin) if len(cand) else (np.argmin(cm[tmin:]) + tmin)
    while tau + 1 < len(cm) and cm[tau + 1] < cm[tau]: tau += 1
    return 69 + 12 * np.log2(SR / tau / 440)


def parse_note(name):
    m = re.search(r'(?<![A-Za-z])([A-G]#?)(-?\d)(?=[_.\s])', name)
    return None if not m else (int(m.group(2)) + 1) * 12 + NOTE[m.group(1)]


class Inst:
    """Pitched instrument from a glob of files named with note names (e.g. *_A#3_*)."""
    def __init__(self, pattern, gain=1.0, octave=None, prefer=None):
        files = sorted(glob.glob(pattern))
        if prefer: files = sorted(files, key=lambda f: 0 if re.search(prefer, f) else 1)
        self.map = {}
        for f in files:
            n = parse_note(os.path.basename(f))
            if n is not None and n not in self.map: self.map[n] = f
        assert self.map, pattern
        if octave is None:  # name convention differs per library: measure it
            offs = []
            for n, f in list(self.map.items())[:: max(1, len(self.map) // 4)][:4]:
                d = yin_midi(load(f)) - n; offs.append(12 * round(d / 12))
            octave = int(np.median(offs))
        self.map = {n + octave: f for n, f in self.map.items()}
        self.gain = gain

    def note(self, midi, dur=None, vel=1.0, rel=0.12):
        root = min(self.map, key=lambda n: (abs(n - midi), n < midi))
        x = load(self.map[root]); r = 2 ** ((midi - root) / 12)
        if abs(r - 1) > 1e-6:
            idx = np.arange(0, len(x) - 1, r)
            x = np.stack([np.interp(idx, np.arange(len(x)), x[:, c]) for c in (0, 1)], 1)
        if dur is not None:
            n = min(len(x), int((dur + rel) * SR)); x = x[:n].copy()
            k = min(n, int(rel * SR)); x[n - k:] *= np.linspace(1, 0, k)[:, None] ** 2
        return x * vel * self.gain


class Hit:
    """Unpitched one-shots; round-robin over the matching files."""
    def __init__(self, pattern, gain=1.0, maxdur=None):
        self.files = sorted(glob.glob(pattern)); assert self.files, pattern
        self.gain, self.maxdur, self.i = gain, maxdur, 0

    def get(self, vel=1.0, k=None, dur=None, rev=False, pitch=0.0):
        f = self.files[(self.i if k is None else k) % len(self.files)]; self.i += 1
        x = load(f)
        if pitch:
            r = 2 ** (pitch / 12); idx = np.arange(0, len(x) - 1, r)
            x = np.stack([np.interp(idx, np.arange(len(x)), x[:, c]) for c in (0, 1)], 1)
        d = dur or self.maxdur
        if d is not None:
            n = min(len(x), int(d * SR)); x = x[:n].copy(); k2 = min(n, int(0.03 * SR)); x[n - k2:] *= np.linspace(1, 0, k2)[:, None]
        if rev: x = x[::-1].copy()
        return x * vel * self.gain


class Bus:
    def __init__(self, dur):
        self.x = np.zeros((int(dur * SR), 2))

    def add(self, sig, t, gain=1.0, pan=0.0, end_at=False):
        if sig is None or len(sig) == 0: return
        i = int(round(t * SR)) - (len(sig) if end_at else 0)
        j0 = max(0, -i); i = max(0, i)
        if i >= len(self.x): return
        s = sig[j0: j0 + len(self.x) - i]
        gl, gr = np.cos((pan + 1) * np.pi / 4) * np.sqrt(2), np.sin((pan + 1) * np.pi / 4) * np.sqrt(2)
        self.x[i:i + len(s), 0] += s[:, 0] * gain * min(1, gl)
        self.x[i:i + len(s), 1] += s[:, 1] * gain * min(1, gr)


def hall(x, seed=5, rt=2.2, pre=0.02):
    """Convolution hall with an exponentially decaying stereo noise IR."""
    n = int(rt * SR); t = np.arange(n) / SR; rng = np.random.default_rng(seed)
    ir = rng.normal(0, 1, (n, 2)) * np.exp(-6.9 * t / rt)[:, None]
    ir[: int(pre * SR)] = 0
    # darken the tail over time
    for c in range(2):
        spec = np.fft.rfft(ir[:, c]); f = np.fft.rfftfreq(n, 1 / SR)
        ir[:, c] = np.fft.irfft(spec / (1 + (f / 6000) ** 2), n)
    ir /= np.sqrt((ir ** 2).sum(0))
    return np.stack([fftconvolve(x[:, c], ir[:, c])[: len(x)] for c in (0, 1)], 1)
