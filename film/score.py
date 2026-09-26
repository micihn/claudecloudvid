"""PORTOKO film score — every cut is a note. Real CC0 recordings only.

The brand hook is played one note per cut. Because the cuts accelerate, the melody starts as
single, spaced piano/harp notes and speeds up into the hook itself, over strings that swell
to 16.0 s, where everything stops dead for the end card. The logo gets one chord and the
switch click from the brand film.
    python3 score.py out.wav
"""
import os, sys
import numpy as np, soundfile as sf
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'showreel', 'audio'))
from sampler import SR, Inst, Hit, Bus, hall
from timeline import CUTS, END, LOGO, DUR

HERE = os.path.dirname(os.path.abspath(__file__))
V = os.environ.get('VSCO', os.path.join(HERE, '..', 'showreel', 'audio', '.samples', 'vsco'))
C = os.environ.get('VCSL', os.path.join(HERE, '..', 'showreel', 'audio', '.samples', 'vcsl'))
X = os.environ.get('CC0SFX', os.path.join(HERE, '..', 'showreel', 'audio', '.samples', 'cc0sfx'))
rng = np.random.default_rng(20)
hv = lambda v, s=0.08: v * rng.uniform(1 - s, 1 + s)

piano = Inst(f'{C}/Chordophones/Zithers/Grand Piano, Steinway B/Sus/*.wav', 0.55, 0)
harp = Inst(f'{V}/Strings/Harp/*.wav', 0.45, 0)
glock = Inst(f'{V}/Percussion/Glock/*.wav', 0.22, 0)
vln = Inst(f'{V}/Strings/Violin Section/susVib/*.wav', 0.4, 12)
vla = Inst(f'{V}/Strings/Viola Section/susvib/*.wav', 0.38, 12)
cel = Inst(f'{V}/Strings/Cello Section/susvib/*.wav', 0.45, 12)
cb = Inst(f'{V}/Strings/Solo Contrabass/Pizz/*.wav', 0.6, 12)
horn = Inst(f'{V}/Brass/F Horn/sus/*.wav', 0.3, 12)
wine = Inst(f'{C}/Idiophones/Friction Idiophones/Wine Glasses/Sustains/Slow/*.wav', 0.35, 0)
tubular = Inst(f'{C}/Idiophones/Struck Idiophones/Tubular Bells 1/*_ff_*.wav', 0.25, 0)
timp_roll = Hit(f'{V}/Percussion/Timpani/Rolls/*_v5_*.wav', 0.45)
cym = Hit(f'{V}/Percussion/susCymb1-cresc-Median*.wav', 0.45)
modeld = Hit(f'{X}/bb - Keyboard Sounds (Mar 2021)/Model D - Switch *.wav', 0.25, 0.2)

HOOK = [('Am', [81, 76, 81, 79, 76, 74, 76]), ('F', [77, 72, 77, 76, 72, 69, 72]),
        ('C', [79, 76, 79, 76, 72, 74, 76]), ('G', [79, 74, 79, 77, 74, 71, 74])]
PAD = {'Am': [45, 57, 60, 64], 'F': [41, 57, 60, 65], 'C': [48, 55, 60, 64], 'G': [43, 55, 59, 62]}
ROOT = {'Am': 33, 'F': 29, 'C': 36, 'G': 31}

bus = Bus(DUR)        # everything up to the hard stop
tail = Bus(DUR)       # the end card, after the stop

# one note per cut, walking through the hook; chords follow the hook's bar
seq = [(ch, n) for ch, notes in HOOK for n in notes]
chord_at = []
for i, t in enumerate(CUTS):
    ch, n = seq[i % len(seq)]
    chord_at.append(ch)
    k = i / (len(CUTS) - 1)                               # 0 -> 1 across the montage
    octave = -12 if i < 12 else 0
    vel = 0.55 + 0.4 * k
    ring = 1.4 if i < 5 else 0.8
    intro = 0.45 if i < 5 else 1.0                          # the opening is barely there
    bus.add(piano.note(n + octave, ring, hv(vel), 0.4), t, 0.9 * intro, 0.15 * np.sin(i))
    bus.add(harp.note(n + octave + 12 if i >= 12 else n + octave, ring, hv(vel * 0.8), 0.3), t + 0.004, 0.55 * intro, -0.3 * np.sin(i))
    if i >= 23: bus.add(glock.note(n + 12, 0.5, hv(0.6 + 0.4 * k)), t, 0.8, 0.3)
    if i < 5: bus.add(piano.note(ROOT[ch] + 12, 2.0, 0.45, 0.8), t, 0.35, -0.2)  # the low notes under the opening

# strings: enter at the first quick cut, swell to the stop; change chord with the hook
spans = []
for i, t in enumerate(CUTS[4:], 4):
    if not spans or spans[-1][2] != chord_at[i]: spans.append([t, None, chord_at[i]])
    spans[-1][1] = CUTS[i + 1] if i + 1 < len(CUTS) else END
for t0, t1, ch in spans:
    k = max(0.0, (t0 - 4.3) / (END - 4.3))
    g = 0.2 + 0.75 * k ** 1.2
    d = t1 - t0 + 0.3
    for j, n in enumerate(PAD[ch]):
        inst = cel if j == 0 else (vla if j < 3 else vln)
        x = inst.note(n, d, 1.0, 0.25)
        a = min(len(x), int(0.25 * SR)); x[:a] *= np.linspace(0.3, 1, a)[:, None]
        bus.add(x, t0, g, -0.3 + j * 0.2)
    if t0 >= 8.15: bus.add(cb.note(ROOT[ch], 0.5, 0.9), t0, 0.7)
    if t0 >= 12.5: bus.add(horn.note(PAD[ch][1] - 12, d, 0.8, 0.2), t0, 0.35 * k)

# the build into the stop
r = timp_roll.get(1.0, k=2, dur=END - 14.2); r = r * np.linspace(0.05, 1, len(r))[:, None] ** 2
bus.add(r, 14.2, 0.9)
bus.add(cym.get(), END, 0.8, 0, end_at=True)

# ---- the end card, after the silence
tail.add(wine.note(69, 3.0, 0.5, 1.0), END + 0.25, 0.25)
for j, n in enumerate((36, 48, 55, 64, 72, 74)):      # C add9, spread
    tail.add(piano.note(n, 2.6, hv(0.55), 1.0), LOGO + j * 0.035, 0.6, -0.3 + j * 0.12)
tail.add(harp.note(84, 2.0, 0.6), LOGO + 0.2, 0.4, 0.3)
tail.add(tubular.note(60, 2.6, 0.7), LOGO, 0.35)
tail.add(modeld.get(k=1), LOGO + 0.9, 0.45)

# mix: the hall rings under the montage, but the stop at END is absolute
wet = hall(bus.x, seed=4, rt=2.2)
mont = bus.x * 0.85 + wet * 0.45
i = int(END * SR); f = int(0.012 * SR)
mont[i - f:i] *= np.linspace(1, 0, f)[:, None]; mont[i:] = 0
end = tail.x * 0.85 + hall(tail.x, seed=5, rt=3.0) * 0.55
mix = mont + end
mix = mix / np.abs(mix).max() * 1.05
mix = np.tanh(mix) / np.tanh(1.05) * 0.89
t = np.arange(len(mix)) / SR
mix *= np.minimum(1, (DUR - t) / 1.0)[:, None]
out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'score.wav')
sf.write(out, mix.astype(np.float32), SR, subtype='PCM_24')
print('wrote', out)
