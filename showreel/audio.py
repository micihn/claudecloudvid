"""Synthesised 20s score for the PORTOKO showreel (120 BPM, cuts on the beat)."""
import numpy as np, wave, sys

SR = 48000; DUR = 20.0; N = int(SR * DUR)
rng = np.random.default_rng(3)
L = np.zeros(N); R = np.zeros(N)
T = np.arange(N) / SR

def add(sig, t0, gain=1.0, pan=0.0):
    i = int(t0 * SR)
    if i >= N: return
    sig = sig[: N - i]
    L[i:i + len(sig)] += sig * gain * np.sqrt(0.5 * (1 - pan))
    R[i:i + len(sig)] += sig * gain * np.sqrt(0.5 * (1 + pan))

def env(n, a, d):
    t = np.arange(n) / SR
    return np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / d)

def lp(x, fc):  # one-pole lowpass, fc may be an array
    fc = np.broadcast_to(fc, x.shape)
    a = 1 - np.exp(-2 * np.pi * fc / SR); y = np.zeros_like(x); s = 0.0
    for i in range(len(x)):
        s += a[i] * (x[i] - s); y[i] = s
    return y

def kick(d=0.45, f0=150, f1=42, click=True):
    n = int(SR * d); t = np.arange(n) / SR
    f = f1 + (f0 - f1) * np.exp(-t * 28); ph = 2 * np.pi * np.cumsum(f) / SR
    s = np.sin(ph) * np.exp(-t / (d * 0.45))
    if click: s[:200] += rng.normal(0, 0.5, 200) * np.linspace(1, 0, 200)
    return np.tanh(s * 1.6)

def boom(d=2.6):
    n = int(SR * d); t = np.arange(n) / SR
    f = 30 + 170 * np.exp(-t * 9); s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.9)
    nz = lp(rng.normal(0, 1, n), 900 * np.exp(-t * 3) + 60) * np.exp(-t / 0.5) * 1.4
    return np.tanh((s + nz) * 1.4)

def hat(d=0.06, open_=False):
    n = int(SR * (0.25 if open_ else d)); x = rng.normal(0, 1, n)
    x = x - lp(x, 7000)
    return x * env(n, 0.001, 0.08 if open_ else 0.018)

def clap():
    n = int(SR * 0.3); x = rng.normal(0, 1, n); x = x - lp(x, 1200)
    e = np.zeros(n)
    for k, o in enumerate([0, 0.011, 0.022]): i = int(o * SR); e[i:] += env(n - i, 0.001, 0.012 if k < 2 else 0.12)
    return x * e * 0.8

def whoosh(d=0.5, rev=False, f0=300, f1=6000):
    n = int(SR * d); t = np.linspace(0, 1, n)
    fc = f0 * (f1 / f0) ** (t if not rev else 1 - t)
    x = rng.normal(0, 1, n); y = lp(x, fc) - lp(x, fc * 0.3)
    e = np.sin(np.pi * t) ** 2 if not rev else t ** 3
    return y * e * 2.5

def riser(d, f0=200, f1=4000):
    n = int(SR * d); t = np.linspace(0, 1, n)
    nz = whoosh(d, False, f0 * 2, f1 * 3) * (t ** 2)
    f = f0 * (f1 / f0) ** (t ** 2); saw = 2 * ((np.cumsum(f) / SR) % 1) - 1
    return nz * 0.6 + lp(saw, 1500 + t * 5000) * 0.25 * t ** 2

def note(freq, d, kind='pluck', a=0.004):
    n = int(SR * d); t = np.arange(n) / SR
    if kind == 'pluck':
        s = sum(np.sin(2 * np.pi * freq * h * t) / h ** 1.3 for h in range(1, 7)) * np.exp(-t / 0.22)
    elif kind == 'bell':
        s = np.sin(2 * np.pi * freq * t + 2.2 * np.exp(-t / 0.5) * np.sin(2 * np.pi * freq * 3.5 * t)) * np.exp(-t / 1.6)
    elif kind == 'sub':
        s = np.tanh(1.5 * np.sin(2 * np.pi * freq * t)) * np.minimum(1, t / 0.01) * np.minimum(1, (d - t) / 0.03)
    return s * np.minimum(1, t / a)

def pad(freqs, d, fc=1200):
    n = int(SR * d); t = np.arange(n) / SR; s = np.zeros(n)
    for f in freqs:
        for det in (-0.12, 0.0, 0.11):
            s += 2 * (((f * (1 + det / 100 * 6)) * t + rng.random()) % 1) - 1
    s = lp(s / (len(freqs) * 3), fc)
    return s * np.minimum(1, t / 0.6) * np.minimum(1, (d - t) / 0.8)

hz = lambda m: 440 * 2 ** ((m - 69) / 12)
A1, F1, C2, G1, E1 = 33, 29, 36, 31, 28

# ---- 0-2 ignition: drone, heartbeat pulses, suck-in
add(pad([hz(45), hz(52), hz(57)], 2.2, 500), 0, 0.5)
for b in (0, 0.5, 1.0, 1.5): add(kick(0.3, 90, 40, False), b, 0.45)
for b in (0.0, 0.5, 1.0, 1.5): add(note(hz(93 + [0, 3, 7, 10][int(b * 2)]), 0.6, 'bell'), b, 0.06, 0.4 - b * 0.4)
add(whoosh(1.0, True, 200, 9000), 1.0, 0.55)
add(riser(1.0, 120, 2000), 1.0, 0.35)

# ---- 2.0 big bang
add(boom(3.0), 2.0, 1.0)
add(whoosh(1.2, False, 6000, 200), 2.0, 0.5, -0.3)
add(note(hz(81), 2.5, 'bell'), 2.0, 0.12, 0.2)

# groove 2.5-7.75 : kick 4-on-floor, claps on 2&4, hats
chords = [(A1, [57, 60, 64]), (F1, [53, 57, 60]), (C2, [55, 60, 64]), (G1, [55, 59, 62])]
for k, b in enumerate(np.arange(2.5, 7.75, 0.5)):
    add(kick(), b, 0.85)
    if b >= 3.0: add(hat(), b + 0.25, 0.22, 0.3)
    if b >= 4.0: add(hat(), b + 0.125, 0.08, -0.3); add(hat(), b + 0.375, 0.08, -0.3)
    if b >= 3.0 and int(round(b * 2)) % 2 == 1: add(clap(), b, 0.35, 0.1)
for i, s0 in enumerate(np.arange(2.0, 8.0, 1.0)):
    root, tri = chords[i % 4]
    for j in range(4):  # 8th-note sub bass pumping
        add(note(hz(root), 0.22, 'sub'), s0 + j * 0.25 + 0.03, 0.32)
    add(pad([hz(m) for m in tri], 1.05, 1400 if s0 >= 5 else 900), s0, 0.28)
# E slam
add(boom(1.2), 4.0, 0.45); add(whoosh(0.2, True, 400, 8000), 3.8, 0.4, -0.7)
add(whoosh(0.55, True, 300, 12000), 4.45, 0.5)  # zoom through O
# word cuts: whooshes + glitch
for w in (5.0, 5.5, 6.0, 6.5, 7.0, 7.25, 7.5):
    add(whoosh(0.18, False, 2000, 9000), w - 0.02, 0.3, rng.uniform(-0.6, 0.6))
for k in range(8): add(hat(0.02) * 3, 5.5 + k * 0.03125, 0.25, 0.8 - k * 0.2)  # rhythm stutter
arp = [69, 72, 76, 79, 81, 79, 76, 72]
for k in range(12): add(note(hz(arp[k % 8] + 12), 0.25), 5.0 + k * 0.25, 0.08, 0.5 * np.sin(k))
add(riser(0.9, 200, 6000), 7.1, 0.5)

# ---- 8.0 portal / orbit: halftime, spacious
add(boom(3.0), 8.0, 0.8)
add(pad([hz(45), hz(57), hz(64), hz(71), hz(76)], 3.8, 1800), 7.9, 0.45)
add(note(hz(A1), 3.4, 'sub'), 8.0, 0.35)
for k, b in enumerate(np.arange(8.0, 11.0, 0.25)):
    m = [81, 84, 88, 91, 93, 88, 84, 79][k % 8]
    for e_, (dly, g) in enumerate([(0, 0.07), (0.375, 0.035), (0.75, 0.018)]):
        add(note(hz(m), 0.4, 'pluck'), b + dly, g, (0.6 if e_ % 2 else -0.6) * (1 if k % 2 else -1))
for b in (9.0, 10.0): add(kick(0.5, 110, 38), b, 0.6)
add(whoosh(0.7, True, 150, 12000), 10.9, 0.7)
add(riser(0.6, 300, 5000), 11.0, 0.35)

# ---- 11.5 flow: build
add(boom(1.5), 11.5, 0.55)
for k, b in enumerate(np.arange(11.5, 14.0, 0.5)):
    add(kick(), b, 0.8)
    for j in range(4): add(hat(), b + j * 0.125, 0.1 + 0.06 * (j == 2), 0.3 if j % 2 else -0.3)
roll = []; tt = 12.5; dt = 0.25
while tt < 13.95: roll.append(tt); tt += dt; dt = max(0.0625, dt * 0.85)
for i, r0 in enumerate(roll): add(clap(), r0, 0.12 + 0.3 * i / len(roll))
for i, s0 in enumerate(np.arange(11.5, 14.0, 1.0)):
    root, tri = chords[i % 4]
    add(note(hz(root), 0.98, 'sub'), s0, 0.3); add(pad([hz(m) for m in tri], 1.0, 1000 + i * 700), s0, 0.25)
add(riser(1.5, 150, 8000), 12.5, 0.65)
add(whoosh(0.4, True, 200, 14000), 13.6, 0.5)

# ---- 14.0 identity drop
add(boom(3.2), 14.0, 1.0)
add(pad([hz(57), hz(64), hz(69), hz(72), hz(76)], 1.2, 5000), 14.0, 0.45)
for m in (69, 76, 81, 88): add(note(hz(m), 2.5, 'bell'), 14.0, 0.07)
for k, b in enumerate(np.arange(14.5, 17.0, 0.5)):
    add(kick(), b, 0.75); add(hat(open_=True), b + 0.25, 0.14, 0.2)
    if k % 2 == 1: add(clap(), b, 0.3)
for i, s0 in enumerate(np.arange(14.0, 17.0, 1.0)):
    root, tri = chords[i % 4]
    for j in range(4): add(note(hz(root), 0.22, 'sub'), s0 + j * 0.25 + 0.03, 0.3)
    add(pad([hz(m) for m in tri], 1.05, 1600), s0, 0.25)
for k in range(12): add(note(hz(72 + [0, 4, 7, 11, 12, 11, 7, 4][k % 8]), 0.3, 'pluck'), 15.0 + k * 0.125, 0.04, 0.4)  # tagline shimmer
add(whoosh(0.9, True, 150, 14000), 16.6, 0.6)
add(riser(0.5, 400, 9000), 17.0, 0.45)

# ---- 17.5 end card: clean resolve
add(boom(2.5), 17.5, 0.75)
for m, g in ((57, 0.1), (64, 0.08), (69, 0.1), (73, 0.07), (76, 0.08), (81, 0.06)): add(note(hz(m), 2.5, 'bell'), 17.5, g)
add(pad([hz(45), hz(57), hz(64), hz(69), hz(73)], 2.5, 1500), 17.5, 0.35)

# ---- reverb (FFT convolution with decaying stereo noise)
def reverb(x, seed, d=1.9):
    n = int(SR * d); t = np.arange(n) / SR
    ir = np.random.default_rng(seed).normal(0, 1, n) * np.exp(-t / (d / 5)); ir[:int(0.015 * SR)] = 0
    ir = lp(ir, 5000); ir /= np.sqrt((ir ** 2).sum())
    m = len(x) + n; F = 1 << (m - 1).bit_length()
    return np.fft.irfft(np.fft.rfft(x, F) * np.fft.rfft(ir, F), F)[:len(x)]
wl, wr = reverb(L, 1), reverb(R, 2)
L2, R2 = L + wl * 0.35, R + wr * 0.35
mix = np.stack([L2, R2], 1)
mix = np.tanh(mix / np.abs(mix).max() * 1.6) * 0.9  # glue + soft limit
fade = np.minimum(1, (DUR - T) / 0.25); mix *= fade[:, None]
mix[: int(0.01 * SR)] *= np.linspace(0, 1, int(0.01 * SR))[:, None]
out = sys.argv[1] if len(sys.argv) > 1 else 'score.wav'
with wave.open(out, 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix * 32767).astype('<i2').tobytes())
print('wrote', out)
