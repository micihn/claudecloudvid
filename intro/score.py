"""PORTOKO intro score — 35 s, real CC0 recordings only, cut to the picture's timeline.

  Lens      a wine-glass drone and a low string bed; each image arrives on one soft piano note,
            walking slowly down the brand hook, with a harp answering.
  Push      a bowed-cymbal and string swell that lands as the horizon opens: a wide F chord.
  Horizon   every cut is a note of the hook (piano + harp, glock later), over strings that build
            with the accelerating cuts, into a hard stop at the end card.
  End       silence, a glass note for "A digital atelier", a C add9 chord and a switch click for
            the wordmark, and a soft string swell under the rising limb.
    python3 score.py out.wav
"""
import os, sys
import numpy as np, soundfile as sf
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'showreel', 'audio'))
from sampler import SR, Inst, Hit, Bus, hall
from timeline import DUR, PUSH, HORIZ, END, ATELIER, LOGO, LENS, CUTS

HERE = os.path.dirname(os.path.abspath(__file__))
S = os.path.join(HERE, '..', 'showreel', 'audio', '.samples')
V = os.environ.get('VSCO', os.path.join(S, 'vsco'))
C = os.environ.get('VCSL', os.path.join(S, 'vcsl'))
X = os.environ.get('CC0SFX', os.path.join(S, 'cc0sfx'))
rng = np.random.default_rng(35)
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
cym_long = Hit(f'{V}/Percussion/susCymb1-cresc-Long*.wav', 0.4)
cym = Hit(f'{V}/Percussion/susCymb1-cresc-Median*.wav', 0.45)
bow = Hit(f'{V}/Percussion/susCymb1-bow-*.wav', 0.3)
modeld = Hit(f'{X}/bb - Keyboard Sounds (Mar 2021)/Model D - Switch *.wav', 0.25, 0.2)

HOOK = [('Am', [81, 76, 81, 79, 76, 74, 76]), ('F', [77, 72, 77, 76, 72, 69, 72]),
        ('C', [79, 76, 79, 76, 72, 74, 76]), ('G', [79, 74, 79, 77, 74, 71, 74])]
PAD = {'Am': [45, 57, 60, 64], 'F': [41, 57, 60, 65], 'C': [48, 55, 60, 64], 'G': [43, 55, 59, 62]}
ROOT = {'Am': 33, 'F': 29, 'C': 36, 'G': 31}


def pad(bus, ch, t0, d, g, lo=True, attack=0.6):
    for j, n in enumerate(PAD[ch]):
        if j == 0 and not lo: continue
        inst = cel if j == 0 else (vla if j < 3 else vln)
        x = inst.note(n, d, 1.0, 0.5)
        a = min(len(x), int(attack * SR)); x[:a] *= np.linspace(0, 1, a)[:, None] ** 1.5
        bus.add(x, t0, g, -0.3 + j * 0.2)


bus = Bus(DUR)        # everything up to the hard stop
tail = Bus(DUR)       # the end card

# ---- lens: sparse and close. One piano note per image, the hook's first phrase, slowly
bus.add(wine.note(69, PUSH + 1.5, 0.45, 1.5), 0.0, 0.22)
bus.add(wine.note(76, PUSH - 3.0, 0.35, 1.5), 3.0, 0.12, 0.4)
LENS_NOTES = [(69, 'Am'), (76, 'Am'), (72, 'F'), (74, 'Am'), (76, 'C'), (72, 'F'), (79, 'C'), (74, 'G')]
for i, (t, (n, ch)) in enumerate(zip(LENS, LENS_NOTES)):
    bus.add(piano.note(n - 12, 2.4, hv(0.45 + 0.03 * i), 1.0), t, 0.75, 0.2 * np.sin(i * 1.7))
    bus.add(piano.note(ROOT[ch] + 12, 2.6, 0.35, 1.0), t + 0.02, 0.3, -0.2)
    bus.add(harp.note(n, 1.4, hv(0.5)), t + 0.7, 0.3 + 0.03 * i, -0.3 * np.sin(i * 1.7))
for t0, t1, ch in [(0.6, 3.0, 'Am'), (3.0, 5.8, 'F'), (5.8, 8.6, 'C'), (8.6, PUSH, 'G')]:
    pad(bus, ch, t0, t1 - t0 + 0.4, 0.07 + 0.012 * t0, lo=True, attack=1.0)
bus.add(bow.get(k=1), 4.4, 0.25, 0.3)

# ---- push: swell into the open horizon
r = cym_long.get(); bus.add(r, HORIZ, 1.0, 0, end_at=True)
r = timp_roll.get(1.0, k=1, dur=HORIZ - PUSH); r = r * np.linspace(0.02, 1, len(r))[:, None] ** 2.2
bus.add(r, PUSH, 0.8)
pad(bus, 'F', PUSH, 1.1, 0.3, attack=0.9)
pad(bus, 'G', PUSH + 1.0, HORIZ - PUSH - 0.9, 0.45, attack=0.7)
for j, n in enumerate((29, 41, 53, 60, 65, 69, 72, 77)):        # the horizon opens: F add, spread wide
    bus.add(piano.note(n, 3.0, hv(0.6), 1.2), HORIZ + j * 0.03, 0.55, -0.35 + j * 0.1)
bus.add(harp.note(84, 2.0, 0.6), HORIZ + 0.25, 0.4, 0.3)

# ---- horizon: one note per cut, walking the hook from its second bar
seq = [(ch, n) for ch, notes in HOOK[1:] + HOOK for n in notes]
chord_at = []
for i, t in enumerate(CUTS):
    ch, n = seq[i % len(seq)]; chord_at.append(ch)
    k = i / (len(CUTS) - 1)
    oct_ = -12 if i < 8 else 0
    vel = 0.5 + 0.42 * k
    if i: bus.add(piano.note(n + oct_, 1.1, hv(vel), 0.4), t, 0.85, 0.15 * np.sin(i))
    bus.add(harp.note(n + oct_ + (12 if i >= 8 else 0), 0.9, hv(vel * 0.8), 0.3), t + 0.004, 0.5, -0.3 * np.sin(i))
    if i >= 14: bus.add(glock.note(n + 12, 0.5, hv(0.55 + 0.4 * k)), t, 0.75, 0.3)
spans = []
for i, t in enumerate(CUTS):
    if not spans or spans[-1][2] != chord_at[i]: spans.append([t, None, chord_at[i]])
    spans[-1][1] = CUTS[i + 1] if i + 1 < len(CUTS) else END
for t0, t1, ch in spans:
    k = (t0 - HORIZ) / (END - HORIZ)
    g = 0.28 + 0.62 * k ** 1.2
    d = t1 - t0 + 0.3
    pad(bus, ch, t0, d, g, attack=0.25)
    if t0 >= 18.5: bus.add(cb.note(ROOT[ch], 0.5, 0.9), t0, 0.7)
    if t0 >= 22.5: bus.add(horn.note(PAD[ch][1] - 12, d, 0.8, 0.2), t0, 0.35 * k)
r = timp_roll.get(1.0, k=2, dur=END - 24.6); r = r * np.linspace(0.05, 1, len(r))[:, None] ** 2
bus.add(r, 24.6, 0.9)
bus.add(cym.get(), END, 0.8, 0, end_at=True)

# ---- the end card, after the stop
tail.add(wine.note(76, 3.2, 0.5, 1.2), ATELIER, 0.25)
tail.add(harp.note(81, 2.0, 0.5), ATELIER + 0.05, 0.3, 0.3)
for j, n in enumerate((36, 48, 55, 64, 72, 74)):             # C add9, spread
    tail.add(piano.note(n, 3.4, hv(0.55), 1.4), LOGO + j * 0.035, 0.6, -0.3 + j * 0.12)
tail.add(harp.note(84, 2.4, 0.6), LOGO + 0.2, 0.4, 0.3)
tail.add(tubular.note(60, 3.0, 0.7), LOGO, 0.33)
tail.add(modeld.get(k=1), LOGO + 1.0, 0.4)
pad(tail, 'C', LOGO + 1.8, DUR - LOGO - 1.8, 0.2, attack=1.8)        # the dawn under the rising limb
tail.add(glock.note(88, 1.5, 0.5), LOGO + 3.4, 0.35, 0.4)

# mix: the hall rings under the montage, but the stop at END is absolute
wet = hall(bus.x, seed=4, rt=2.4)
mont = bus.x * 0.85 + wet * 0.5
i = int(END * SR); f = int(0.012 * SR)
mont[i - f:i] *= np.linspace(1, 0, f)[:, None]; mont[i:] = 0
end = tail.x * 0.85 + hall(tail.x, seed=5, rt=3.2) * 0.6
mix = mont + end
mix = mix / np.abs(mix).max() * 1.05
mix = np.tanh(mix) / np.tanh(1.05) * 0.89
t = np.arange(len(mix)) / SR
mix *= np.minimum(1, (DUR - t) / 1.2)[:, None]
out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'score.wav')
sf.write(out, mix.astype(np.float32), SR, subtype='PCM_24')
print('wrote', out)
