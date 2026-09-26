"""PORTOKO teaser — 30 s, slow and warm. Real CC0 recordings only (see CREDITS.md).

60 BPM, one bar = 4 s. The hook from the brand film returns at half speed and is
passed between soloists: piano -> cello -> clarinet -> solo violin -> strings + flute.
  0  Am   room: wine glass, a few piano notes             (shot: tangled thread)
  4  Am   piano plays the hook, strings breathe in
  8  F    cello section takes it
 12  C    clarinet; one soft key jingle (the untangling)
 16  G    solo violin, harp arpeggios
 20  Am   full strings + flute: the warm peak
 24  F G  turn toward home
 26  C    resolve: piano, tubular bell, horn; the switch click on the logo
Usage: python3 teaser_score.py out.wav
"""
import os, sys
import numpy as np, soundfile as sf
from sampler import SR, Inst, Hit, Bus, hall

HERE = os.path.dirname(os.path.abspath(__file__))
V = os.environ.get('VSCO', os.path.join(HERE, '.samples', 'vsco'))
C = os.environ.get('VCSL', os.path.join(HERE, '.samples', 'vcsl'))
X = os.environ.get('CC0SFX', os.path.join(HERE, '.samples', 'cc0sfx'))
DUR = 30.0
ST = 0.25  # one step of the hook (a 16th at 60 BPM)
rng = np.random.default_rng(30)
hum = lambda s=0.012: rng.uniform(-s, s)
hv = lambda v, s=0.1: v * rng.uniform(1 - s, 1 + s)

piano = Inst(f'{C}/Chordophones/Zithers/Grand Piano, Steinway B/Sus/*.wav', 0.5, 0)
cel = Inst(f'{V}/Strings/Cello Section/susvib/*.wav', 0.5, 12)
vla = Inst(f'{V}/Strings/Viola Section/susvib/*.wav', 0.4, 12)
vln = Inst(f'{V}/Strings/Violin Section/susVib/*.wav', 0.4, 12)
solo = Inst(f'{V}/Strings/Solo Violin/Arco Vib/*_p.wav', 0.45, 0)
clar = Inst(f'{V}/Woodwinds/Clarinet/susLong/*_v2_*.wav', 0.45, 12)
flute = Inst(f'{V}/Woodwinds/Flute/susvib/*.wav', 0.38, 12)
horn = Inst(f'{V}/Brass/F Horn/sus/*.wav', 0.35, 12)
harp = Inst(f'{V}/Strings/Harp/*.wav', 0.42, 0)
wine = Inst(f'{C}/Idiophones/Friction Idiophones/Wine Glasses/Sustains/Slow/*.wav', 0.4, 0)
tubular = Inst(f'{C}/Idiophones/Struck Idiophones/Tubular Bells 1/*_ff_*.wav', 0.3, 0)
chimes = Inst(f'{C}/Idiophones/Struck Idiophones/Hand Chimes/*.wav', 0.25, 0)
timp_roll = Hit(f'{V}/Percussion/Timpani/Rolls/*_v5_*.wav', 0.35)
cym_bow = Hit(f'{V}/Percussion/susCymb1-bow-1.wav', 0.25)
keys = Hit(f'{X}/100-CC0-wood-metal-SFX/keys_*.ogg', 0.3)
modeld = Hit(f'{X}/bb - Keyboard Sounds (Mar 2021)/Model D - Switch *.wav', 0.3, 0.2)
glass_tap = Hit(f'{X}/kenney_impactsounds/Audio/impactGlass_light_*.ogg', 0.25)

CH = {
    'Am': (45, [57, 60, 64, 69], [45, 52, 57, 60, 64]), 'F': (41, [57, 60, 65, 69], [41, 48, 53, 57, 60]),
    'C': (48, [55, 60, 64, 67], [36, 43, 48, 52, 55]), 'G': (43, [55, 59, 62, 67], [43, 50, 55, 59, 62]),
}
HOOK = {
    'Am': {0: 81, 3: 76, 6: 81, 8: 79, 10: 76, 12: 74, 14: 76},
    'F': {0: 77, 3: 72, 6: 77, 8: 76, 10: 72, 12: 69, 14: 72},
    'C': {0: 79, 3: 76, 6: 79, 8: 76, 10: 72, 12: 74, 14: 76},
    'G': {0: 79, 3: 74, 6: 79, 8: 77, 10: 74, 12: 71, 14: 74},
}
bus = Bus(DUR)


def hook(inst, t0, chord, trans=0, gain=1.0, pan=0.0, steps=16, rel=0.5, legato=1.15):
    h = HOOK[chord]; ks = sorted(k for k in h if k < steps)
    for i, k in enumerate(ks):
        nxt = ks[i + 1] if i + 1 < len(ks) else steps
        bus.add(inst.note(h[k] + trans, (nxt - k) * ST * legato, hv(1.0 if k in (0, 6) else 0.85), rel), t0 + k * ST + hum(), gain, pan)


def swell(x, secs):
    if secs <= 0: return x
    k = min(len(x), int(secs * SR)); x = x.copy(); x[:k] *= np.linspace(0, 1, k)[:, None] ** 1.5
    return x


def pad(t0, chord, dur, gain=1.0, rise=0.0):
    root, up, _ = CH[chord]
    bus.add(swell(cel.note(root - 12 if root > 40 else root, dur, 1.0, 1.2), rise), t0 + hum(0.03), gain, -0.3)
    for i, n in enumerate(up[:3]):
        bus.add(swell((vla if i < 2 else vln).note(n, dur, 0.8, 1.2), rise), t0 + hum(0.03), gain * 0.8, -0.2 + i * 0.25)


def piano_bed(t0, chord, gain=0.6, bars=1):
    """Slow broken chords in 8ths, left hand low, right hand answering."""
    _, _, lh = CH[chord]
    pat = [0, 2, 3, 4, 3, 2, 1, 2]
    for b in range(bars):
        for j, p in enumerate(pat):
            bus.add(piano.note(lh[p], 1.2, hv(0.55 if j else 0.75), 0.6), t0 + b * 4 + j * 0.5 + hum(0.01), gain, -0.25 + p * 0.1)


# 0-4: the room
bus.add(wine.note(69, 4.5, 0.9, 1.0), 0.0, 0.55, -0.2)
bus.add(wine.note(76, 3.6, 0.7, 1.0), 0.9, 0.35, 0.3)
for s, n in ((0, 69), (3, 64), (6, 69)):        # the hook, three notes, alone
    bus.add(piano.note(n + 12, 2.0, 0.7, 0.8), 1.0 + s * ST * 2 + hum(), 0.55, 0.15)
bus.add(glass_tap.get(k=4), 3.4, 0.25, 0.6)

# 4-8: piano hook, strings breathe in
piano_bed(4.0, 'Am', 0.3)
hook(piano, 4.0, 'Am', -12, 0.4, 0.2, legato=1.6, rel=0.9)
pad(4.0, 'Am', 4.2, 0.45, rise=2.5)

# 8-12: cello takes the melody
piano_bed(8.0, 'F', 0.4)
hook(cel, 8.0, 'F', -24, 0.8, -0.2)
pad(8.0, 'F', 4.2, 0.45)

# 12-16: clarinet; the untangling moment
piano_bed(12.0, 'C', 0.32)
hook(clar, 12.0, 'C', -12, 0.55, 0.25)
pad(12.0, 'C', 4.2, 0.38)
bus.add(keys.get(k=3), 12.0, 0.22, -0.5)
bus.add(chimes.note(84, 2.5, 0.7), 12.1, 0.3, 0.5)

# 16-20: solo violin over harp
for i, n in enumerate([43, 50, 55, 59, 62, 67, 71, 74] * 2):
    bus.add(harp.note(n, 1.4, hv(0.75)), 16.0 + i * 0.25 + hum(0.008), 0.5, -0.5 + (i % 8) * 0.14)
hook(solo, 16.0, 'G', 0, 0.85, 0.1)
pad(16.0, 'G', 4.2, 0.55)
r = timp_roll.get(1.0, k=0, dur=1.6); r = r * np.linspace(0.02, 1, len(r))[:, None] ** 2
bus.add(r, 18.4, 0.5)
bus.add(cym_bow.get(), 20.0, 0.5, 0, end_at=True)

# 20-24: the warm peak
hook(vln, 20.0, 'Am', 0, 0.75, -0.2)
hook(flute, 20.0, 'Am', 0, 0.5, 0.3)
hook(cel, 20.0, 'Am', -24, 0.45, -0.4)
piano_bed(20.0, 'Am', 0.5)
pad(20.0, 'Am', 4.2, 0.75, rise=0.8)
for n in (57, 64): bus.add(horn.note(n, 4.0, 0.7, 1.2), 20.0, 0.6)

# 24-26: turn toward home
for t0, ch in ((24.0, 'F'), (25.0, 'G')):
    hook(vln, t0, ch, 0, 0.6, -0.2, steps=4, legato=1.3)
    pad(t0, ch, 1.2, 0.6)
    bus.add(piano.note(CH[ch][2][0], 1.5, 0.7, 0.6), t0, 0.5)

# 26-30: resolve to C
for i, n in enumerate((36, 48, 55, 60, 64, 67, 72, 76)):
    bus.add(piano.note(n, 4.0, hv(0.65), 1.0), 26.0 + i * 0.07, 0.55, -0.4 + i * 0.1)
pad(26.0, 'C', 3.6, 0.65)
for n in (48, 55, 64): bus.add(horn.note(n, 3.5, 0.6, 1.2), 26.0, 0.5)
bus.add(vln.note(79, 3.5, 0.6, 1.2), 26.0, 0.4, 0.3)
bus.add(tubular.note(60, 4.0, 0.8), 26.0, 0.45)
bus.add(wine.note(79, 3.8, 0.8, 1.0), 26.2, 0.35, 0.3)
for i, n in enumerate((72, 76, 79, 84)): bus.add(harp.note(n, 2.0, 0.6), 26.4 + i * 0.12, 0.35, 0.4)
bus.add(modeld.get(k=1), 27.2, 0.7); bus.add(glass_tap.get(k=0), 27.22, 0.35, 0.2)

# mix: big warm hall, a gentle high roll-off, soft limiter
dry = bus.x
wet = hall(dry, seed=9, rt=3.4, pre=0.03)
mix = dry * 0.75 + wet * 0.6
spec = np.fft.rfft(mix, axis=0); f = np.fft.rfftfreq(len(mix), 1 / SR)
mix = np.fft.irfft(spec / np.sqrt(1 + (f / 9000) ** 4)[:, None], len(mix), axis=0)
mix = mix / np.abs(mix).max() * 1.1
mix = np.tanh(mix) / np.tanh(1.1) * 0.89
t = np.arange(len(mix)) / SR
mix *= (np.minimum(1, t / 0.4) * np.minimum(1, (DUR - t) / 1.2))[:, None]
out = sys.argv[1] if len(sys.argv) > 1 else 'teaser_score.wav'
sf.write(out, mix.astype(np.float32), SR, subtype='PCM_24')
print('wrote', out)
